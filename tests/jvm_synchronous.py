"""Install immutable synchronous JVM selections, compile sources and check VM grants."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from separate_compilation import cgroup_record
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install
from imports import inspect
from guest_profile import Profile

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository","toolchain","sysroots","bundle","vm","xmake","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--commit",required=True)
    opts=parser.parse_args()
    for key in ("repository","toolchain","sysroots","bundle","vm","xmake","output"):
        setattr(opts,key,getattr(opts,key).resolve())
    cgroup=cgroup_record()
    assert int(cgroup["memory_max"])==68719476736 and int(cgroup["swap_max"])==0
    out=opts.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    (out/"tmp").mkdir()
    os.environ["TMPDIR"]=str(out/"tmp")
    report=dict(complete=False,cgroup=cgroup,commit=opts.commit,cases=[],selections={},guests={})
    def save(): (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    for lang,suffix in (("java","java"),("kotlin","kt")):
        def retrieve(options):
            source=Source(opts.commit,opts.repository.resolve())
            result=install(source,"unitree",lang,out/"install",options)
            return Path(result["directory"]),source.requested
        try: retrieve([])
        except (ValueError,RuntimeError): pass
        else: raise AssertionError("full language incorrectly registered")
        sdk,requested=retrieve(["--component","synchronous-aot"])
        other="java" if lang=="kotlin" else "kotlin"
        assert "bin/wr"+lang in requested and "language/"+lang+"/xmake/adapter.lua" in requested
        assert not any(p.startswith(("platform/",)) and not p.startswith("platform/unitree/") for p in requested)
        assert not any(p.startswith(("language/"+other+"/","examples/"+other+"/")) or p=="bin/wr"+other for p in requested)
        report["selections"][lang]=requested
        project=out/(lang+"-project");shutil.copytree(sdk/"examples"/lang/"synchronous-aot",project)
        env=dict(os.environ,TMPDIR=str(out/"tmp"),XMAKE_GLOBALDIR=str(out/(lang+"-xmake")),UWVM_ROS_SDK_ROOT=str(sdk),
                 WROS_TOOLCHAIN=str(opts.toolchain.resolve()),WROS_SYSROOTS=str(opts.sysroots.resolve()),
                 WROS_JVM_BUNDLE=str(opts.bundle.resolve()),WROS_VM=str(opts.vm.resolve()),PYTHONDONTWRITEBYTECODE="1")
        def run(name,args,expected=True,needle=None,**extra):
            proc=subprocess.run(list(map(str,args)),cwd=project,env=dict(env,**extra),capture_output=True,timeout=220)
            log=proc.stdout+proc.stderr; key=lang+"-"+name; (out/(key+".log")).write_bytes(log)
            ok=(proc.returncode==0)==expected and (not needle or needle in log)
            report["cases"].append(dict(name=key,argv=list(map(str,args)),exit=proc.returncode,passed=ok))
            save();print(key,proc.returncode,ok,flush=True)
            if not ok: raise RuntimeError(log.decode(errors="replace")[-2200:])
        run("xmake-configure",[opts.xmake,"f","-c","-y","-a","wasm32"])
        run("xmake-build",[opts.xmake,"-j1","robot"])
        run("xmake-hidden",[opts.xmake,"run","robot"],False,b"ROS scene interface is hidden",WROS_RUN_QUERIES="")
        run("xmake-abi",[opts.xmake,"run","robot"],WROS_RUN_QUERIES="abi")
        guest=next(project.glob("build/*/wasm32/*/robot.wasm"))
        assert {(x["module"],x["name"]) for x in inspect(guest.read_bytes())}=={("uwvm_ros_v2","abi")}
        prior=guest.read_bytes()
        base=[sdk/"bin"/("wr"+lang),"--toolchain",opts.toolchain.resolve(),"--sysroots",opts.sysroots.resolve(),"--bundle",opts.bundle.resolve(),
              "--main-class","example.Main","-o",guest]
        for mode in ([],["--mte"],["--no-mte"]):
            run("unsigned-"+("-".join(mode) or "default"),[*base,*mode,project/("Main."+suffix)],False,b"no signed")
        for label,java_body,kt_body,diagnostic in (
              ("threads","Thread.yield();","Thread.yield()",b"java/lang/Thread"),
              ("catch","try { throw new Error(); } catch (Error ignored) {}","try { throw Error() } catch (x: Error) {}",b"exception handler"),
              ("monitor","synchronized(args) { System.gc(); }","synchronized(args) { System.gc() }",b"unsupported synchronous"),
              ("buffers","java.nio.ByteBuffer.allocateDirect(8);","java.nio.ByteBuffer.allocateDirect(8)",b"java/nio/ByteBuffer")):
            rejected=project/("Negative."+suffix)
            rejected.write_text("package example; class Main { public static void main(String[] args) {"+java_body+"} }" if lang=="java" else
                                '@file:JvmName("Main")\npackage example\nfun main(args:Array<String>){'+kt_body+'}')
            run(label,[*base,"--legacy-mte",rejected],False,diagnostic)
            assert guest.read_bytes()==prior
        for label,java_decl,kt_decl,diagnostic in (
                ("inherited-member", "class Main { public static void main(String[] a){ new Main().hashCode(); } }",
                 'class Child; fun main(a:Array<String>) { Child().hashCode() }', b"hashCode()I"),
                ("native", "class Main { static native void host(); public static void main(String[] a){} }",
                 'external fun host(); fun main(a:Array<String>) {}', b"unsupported synchronous JVM feature: host"),
                ("missing-entry", "class Main { public static void main(int wrong){} }",
                 'fun main(wrong:Int) {}', b"entry must declare public static void main(String[])")):
            rejected.write_text("package example; " + java_decl if lang == "java" else
                                '@file:JvmName("Main")\npackage example\n' + kt_decl)
            run(label,[*base,"--legacy-mte",rejected],False,diagnostic)
            assert guest.read_bytes()==prior
        entry=project/("GuardApplication."+suffix)
        guard=out/(lang+"-guard.wasm")
        run("build-guard",[sdk/"bin"/("wr"+lang),"--legacy-mte","--toolchain",opts.toolchain.resolve(),"--sysroots",opts.sysroots.resolve(),
                           "--bundle",opts.bundle.resolve(),"--main-class","example.GuardApplication","-o",guard,entry])
        ops=("capability.open","capability.close","guard.create","guard.trigger","guard.take")
        assert {(x["module"],x["name"]) for x in inspect(guard.read_bytes())}=={("uwvm_ros_v2",n) for n in ops}
        report["guests"][lang]=hashlib.sha256(guard.read_bytes()).hexdigest()
        for engine in ("int","aot"):
            args=[opts.vm,*Profile().uwvm_feature_flags(),"--debug-fault-action","exit","--runtime-"+engine,"--runtime-compile-threads","0",
                  "--runtime-llvm-jit-cache-path","disable","--wasm-set-main-module-name","main","--ros-scene-create","robot","--ros-scene-bind","robot","main"]
            for op in ops:args+=["--ros-scene-interface","robot",op,"allow"]
            run(engine+"-zero-grant",[*args,"--run",guard],False,b"unreachable")
            run(engine+"-guard",[*args,"--ros-scene-grant","robot","signal","guard","signal","local","guard.create,guard.trigger,guard.take","--run",guard])
    report["complete"]=True;save()

if __name__=="__main__":
    main()
