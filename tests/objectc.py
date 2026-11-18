#!/usr/bin/env python3
"""Build and execute genuine GNUstep classes under allowed and denied u2ros policy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"install"))
from guest_profile import Profile
from frontend import audit
from imports import inspect
from separate_compilation import cgroup_record

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime",required=True,type=Path)
    parser.add_argument("--toolchain",required=True,type=Path)
    parser.add_argument("--objc-clang",required=True,type=Path)
    parser.add_argument("--objc-runtime",required=True,type=Path)
    parser.add_argument("--sysroots",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--target",choices=("wasm32","wasm64"),required=True)
    parser.add_argument("--eh",action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument("--mode",choices=("strict","candidate","off"),required=True)
    args=parser.parse_args()
    group=cgroup_record()
    assert int(group['memory_max'])==68719476736 and int(group['swap_max'])==0
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    os.environ["TMPDIR"]=str(out)
    def sha(path):
        with path.open('rb') as f: return hashlib.file_digest(f,"sha256").hexdigest()
    source=ROOT/"tests/objectc/dispatch.m";guest=out/'app.wasm';vm=args.runtime.resolve()
    inputs=[source, ROOT/"tests/objectc/neighbors.m", Path(__file__), args.objc_clang,args.objc_runtime/"runtime.json",args.objc_runtime/"libobjc.a",
            args.toolchain/"bin/clang",args.toolchain/"bin/wasm-ld",vm,args.sysroots]
    report={"complete":False,"cgroup":group,"inputs":{str(p):sha(p) for p in inputs},"cases":[]}
    def save(): (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    def run(label,argv,denied=False,err=None):
        cmd=list(map(str,argv));p=subprocess.run(cmd,cwd=out,capture_output=True,timeout=120)
        log=p.stdout+p.stderr;(out/(label+".log")).write_bytes(log)
        ok=(p.returncode==0 if not denied else (p.returncode!=0 and err.encode() in log))
        report["cases"].append({"case":label,"argv":cmd,"exit":p.returncode,"expected_success":not denied,"passed":ok});save()
        print(label,p.returncode,ok,flush=True)
        if not ok: raise RuntimeError(log.decode(errors="replace")[-2000:])
    bits=int(args.target[4:]);profile=Profile(bits,mte=args.mode!="off", exceptions="eh" if args.eh else "noeh")
    common=[ROOT/"bin/wrobjc","--target",args.target,"--toolchain",args.toolchain.resolve(),
            "--sysroots",args.sysroots.resolve(),"--objc-runtime",args.objc_runtime.resolve(),"--objc-clang",args.objc_clang.resolve(),
            {"strict":"--mte","candidate":"--legacy-mte","off":"--no-mte"}[args.mode], "--eh" if args.eh else "--no-eh","-O3","-g"]
    # Check separate compilation through the normal frontend and its WROS object annotations.
    obj=out/"dispatch.o"
    run("compile",[ *common,"-c",source,"-o",obj])
    run("link",[*common,"--reactor","--export","_start",obj,"-o",guest])
    data=guest.read_bytes();audit(data,profile);imports=inspect(data);report["imports"]=imports;report["guest"]=sha(guest)
    needs={("uwvm_ros_v2",n) for n in ("abi","capability.open","capability.close")}
    clock="clock_time_get"+("_wasm64" if bits==64 else "")
    assert {(i["module"],i["name"]) for i in imports}==needs|{("wasi_snapshot_preview1",clock)}
    neighbors=out/"neighbors.wasm"
    if profile.mte:
        run("compile-neighbors", [*common, "--reactor", "--export", "_start", ROOT/"tests/objectc/neighbors.m", "-o", neighbors])
        report["neighbors_sha256"]=sha(neighbors)
    for engine in ("int","aot"):
        flags=[vm,*profile.uwvm_feature_flags(),"--debug-fault-action","exit","--runtime-"+engine,"--runtime-compile-threads","0",
               "--runtime-llvm-jit-cache-path","disable","--wasm-set-main-module-name","main",
               "--wasip1-single-create","main","--wasip1-single-enable","main","--wasip1-single-interface","main",clock,"allow",
               "--wasip1-single-grant","main","realtime-clock","--ros-scene-create","robot","--ros-scene-bind","robot","main"]
        for op in ("abi","capability.open","capability.close"):flags+=["--ros-scene-interface","robot",op,"allow"]
        for active in (True,False) if profile.mte else (False,):
            controls=[] if active else ["--runtime-disable-memtag"]
            if profile.mte:
                run(engine+f"-{active}-neighbors",[*flags,*controls,"--run",neighbors])
            run(engine+f"-{active}-denied",[*flags,*controls,"--run",guest],True,"unreachable")
            run(engine+f"-{active}-allowed",[*flags,*controls,"--ros-scene-grant","robot","signal","guard","signal","local","guard.create","--run",guest])
    # A new host import outside the WROS ABI must be rejected without replacing the last valid output.
    forbidden=out/"fd.m"
    forbidden.write_text('__attribute__((import_module("env"),import_name("native_escape"))) extern int native_escape(void);\n'
                         'void _start(void){(void)native_escape();}\n')
    run("unregistered-import",[*common,"--reactor","--export","_start",forbidden,"-o",guest],True,"unauthorized import")
    assert sha(guest)==report["guest"]
    report["complete"]=all(sha(Path(name))==identity for name,identity in report["inputs"].items());save()
    return int(not report["complete"])

if __name__=="__main__": raise SystemExit(main())
