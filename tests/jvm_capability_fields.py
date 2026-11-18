"""Verify nested JVM capability references against the installed wire catalogue and a simulated ROS clock."""
import argparse
import json
import os
from pathlib import Path
import sys
import subprocess

from separate_compilation import cgroup_record
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"install"))
from bootstrap import Source,install
from guest_profile import Profile
from imports import inspect

SCHEDULE=("capability.open","capability.close","clock.create","clock.read","clock.update",
          "timer.create","timer.reset","timer.take","timer.cancel","resource.close")


def encode_field(schemas,name,kind,positions,wire,optional):
    if kind.startswith("array<"):
        wire.extend((2).to_bytes(8,"little"))
        for _ in range(2): encode_field(schemas,name,kind[6:-1],positions,wire,optional)
    elif kind.startswith("optional<"):
        wire.extend(int(optional).to_bytes(8,"little"))
        if optional: encode_field(schemas,name,kind[9:-1],positions,wire,optional)
    elif name=="capability" or name.endswith(("_capability","_capabilities")):
        assert kind=="u64"
        positions.append(len(wire))
        wire.extend(bytes(8))
    elif kind in ("text","bytes"):
        data=b"odd" if kind=="text" else b"\x11\x22\x33\x44\x55"
        wire.extend(len(data).to_bytes(8,"little")+data)
    elif kind in ("u64","i64","bool","f64"):wire.extend((1).to_bytes(8,"little"))
    elif kind in schemas and "fields" in schemas[kind]:
        for n,t in schemas[kind]["fields"]: encode_field(schemas,n,t,positions,wire,optional)
    else:
        raise ValueError("unsupported independent test encoder type "+kind)


def fixtures(registry):
    cases={}
    for op in registry["operations"]:
        if op["name"]=="capability.close": continue
        try:
            rows=[]
            for optional in (False,True):
                positions=[]; wire=bytearray()
                for item in op["request"]: encode_field(registry["schemas"],item["name"],item["type"],positions,wire,optional)
                if positions: rows.append((positions,wire))
        except ValueError:continue
        if rows: cases[op["name"]]=rows
    assert len(cases)==24
    return cases


def field_guest(java,cases):
    header="""package example; import wros.scene.Calls; final class Fields {
    static void ck(boolean ok){ if(!ok) throw new AssertionError(); }
    public static void main(String[] args){ Calls f=new Calls(8192,8); Calls auth=new Calls(8,8);
    ck(auth.capabilityOpen(new byte[]{111,116,104,101,114})==0);
    byte[] output={85}; long[] written={123};""" if java else '''@file:JvmName("Fields")
    package example
    import wros.scene.Calls
    private fun ck(ok:Boolean){if(!ok) throw AssertionError()}
    fun main(args:Array<String>){val f=Calls(8192,8); val auth=Calls(8,8)
    ck(auth.capabilityOpen(byteArrayOf(111,116,104,101,114))==0)
    val output=byteArrayOf(85); val written=longArrayOf(123)'''
    chunks=[]
    for name, rows in cases.items():
        words=name.replace("_",".").split("."); member=words[0]+"".join(s[0].upper()+s[1:] for s in words[1:])
        for positions,wire in rows:
            # Compress the fixture, leaving all zero placeholders and padding unmodified.
            number=len(chunks); v="r"+str(number); a="a"+str(number)
            if java:
                block=f"byte[] {v}=new byte[{len(wire)}]; Calls[] {a}=new Calls[{len(positions)}];\n"
                block+=f"for(int j=0;j<{a}.length;j++) {a}[j]=auth;\n"
            else:
                block=f"val {v}=ByteArray({len(wire)}); val {a}=arrayOf("+",".join("auth" for _ in positions)+")\n"
            block+="\n".join(f"{v}[{i}]={b};" for i,b in enumerate(wire) if b)
            field=f"f.{member}({v},output,written,{a})"
            # Interface deny (13) can be reached only after successful reference packing.
            block+=f"\nck({field}==13 && {v}[{positions[0]}]"+("==0" if java else ".toInt()==0")+")\n"
            block+=f"{v}[{positions[-1]}]=42; ck({field}==22);\n"
            chunks.append(block.replace(")\n",");\n") if java else block)
    end="ck(output[0]==85 && written[0]==123);ck(auth.capabilityClose()==0);}}" if java else "ck(output[0].toInt()==85 && written[0]==123L);ck(auth.capabilityClose()==0)}"
    return header+"\n"+"\n".join(chunks)+"\n"+end


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("sdk","toolchain","sysroots","bundle","vm","output"):p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--commit",required=True)
    p.add_argument("--language",choices=("java","kotlin"),required=True)
    opts=p.parse_args()
    group=cgroup_record()
    assert int(group["memory_max"])==68719476736 and int(group["swap_max"])==0
    out=opts.output.resolve();out.mkdir(exist_ok=False)
    sdk=Path(install(Source(opts.commit,opts.sdk.resolve()),"unitree",opts.language,out/"install",["--component","synchronous-aot"])["directory"])
    os.environ["TMPDIR"]=str(out)
    report={"commit":opts.commit,"cgroup":group,"complete":False,"cases":[]}
    def run(name,args):
        r=subprocess.run(list(map(str,args)),cwd=out,capture_output=True,timeout=300)
        (out/(name+".log")).write_bytes(r.stdout+r.stderr)
        report["cases"].append({"name":name,"exit":r.returncode})
        (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
        if r.returncode:raise ValueError(name+" "+(r.stdout+r.stderr)[-1200:].decode(errors="replace"))
    java=opts.language=="java"; ext="java" if java else "kt"
    suite=fixtures(json.loads((sdk/"share/abi/ros.json").read_text()))
    report["layouts"]={n:[len(p) for p,_ in rows] for n,rows in suite.items()}
    src=out/("Fields."+ext);src.write_text(field_guest(java,suite))
    full=("capability.open","capability.close",*suite)
    docs=sdk/"examples"/opts.language/"synchronous-aot"/("Schedule."+ext)
    for title,source,ops in (("Fields",src,full),("Schedule",docs,SCHEDULE)):
        guest=out/(title+".wasm")
        cli=[sys.executable,sdk/"bin"/("wrjava" if java else "wrkt"),"--toolchain",opts.toolchain.resolve(),
             "--sysroots",opts.sysroots.resolve(),"--bundle",opts.bundle.resolve(),"--legacy-mte",
             "--main-class","example."+title]
        options=[a for n in ops for a in ("--ros-operation",n)]
        run(title+"-compile",[*cli,*options,source,"-o",guest])
        assert {(i["module"],i["name"]) for i in inspect(guest.read_bytes())}=={("uwvm_ros_v2",n) for n in ops}
        flags=["--wasm-set-main-module-name","main","--ros-scene-create","robot","--ros-scene-bind","robot","main"]
        for n in ops:
            flags+=["--ros-scene-interface","robot",n,"deny" if title=="Fields" and n in suite else "allow"]
        flags+=["--ros-scene-grant","robot","other","guard","other","local","guard.create"]
        if title=="Schedule":
            flags+=["--ros-scene-grant","robot","time","clock.ros","time","local","clock.create,clock.read,clock.update,resource.close",
                    "--ros-scene-grant","robot","timer","timer","timer","local","timer.create,timer.reset,timer.take,timer.cancel,resource.close"]
        for engine in ("int","aot"):
            run(title+"-"+engine,[opts.vm,*Profile().uwvm_feature_flags(),"--debug-fault-action","exit",
              "--runtime-"+engine,"--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable",*flags,"--run",guest])
    report["complete"]=True
    (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":main()
