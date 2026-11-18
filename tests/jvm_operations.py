"""Verify selected JVM ROS imports, per-import visibility and a stateful guard transaction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

from separate_compilation import cgroup_record
import shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"install"))
sys.path.insert(0,str(ROOT/"language/jvm"))
from guest_profile import Profile
from imports import inspect
from artifacts import sections
from private_exports import keep_private_memory
from compiler import compiler_environment
from bootstrap import Source, install
from operations import method, SPECIAL

GUARD=("capability.open","capability.close","guard.create","guard.trigger","guard.take")


def entire_catalog(java,names):
    # The deployment explicitly denies every import, including each introspection operation.
    # Test the guest reads the VM status and never publishes a denied reply.
    if java:
        begin = """package example; import wros.scene.Calls;
        final class Catalog { public static void main(String[] args) {
        Calls api=new Calls(8,8); byte[] empty=new byte[0], out={85}; long[] written={123};
        Calls.abi(); int opened=api.capabilityOpen(new byte[]{110});
        int closed=api.capabilityClose(); if(opened!=13 || closed!=9) throw new AssertionError();
        """
        case = "if(api.%s(empty,out,written)!=13 || out[0]!=85 || written[0]!=123) throw new AssertionError();"
        end = "} }"
    else:
        begin = """@file:JvmName("Catalog")
        package example
        import wros.scene.Calls
        fun main(args:Array<String>){
          val api=Calls(8,8); val empty=ByteArray(0); val out=byteArrayOf(85); val written=longArrayOf(123L)
          Calls.abi(); val opened=api.capabilityOpen(byteArrayOf(110)); val closed=api.capabilityClose()
          if(opened!=13 || closed!=9) throw AssertionError()
        """
        case = "if(api.%s(empty,out,written)!=13 || out[0].toInt()!=85 || written[0]!=123L) throw AssertionError()"
        end = "}"
    return begin+"\n".join(case%method(n) for n in names if n not in SPECIAL)+"\n"+end+"\n"


def observation(java):
    def text(value):
        raw=value.encode("ascii")
        return len(raw).to_bytes(8,"little")+raw
    def literal(*fields):
        packed=b"".join(text(f) for f in fields)+bytes(8)
        return ("new byte[]{" if java else "byteArrayOf(")+",".join(map(str,packed))+("}" if java else ")")
    exact=literal("rosv2","clock.read")
    legacy=literal("preloaddl","")
    unknown=literal("rosv2","does.not.exist")
    wrong=literal("missing")
    disabled=literal("wasip1","")
    if java:
        return f"""package example; import wros.scene.Calls;
        final class Observe {{
            static void check(boolean ok) {{if(!ok) throw new AssertionError();}}
            public static void main(String[] args) {{
                Calls f=new Calls(128,65536); byte[] page=new byte[65536]; long[] n=new long[1];
                check(f.permissionReport({exact},page,n)==0 && n[0]>40 && page[0]==1 && page[8]==1 && page[24]==1);
                check(f.permissionReport({disabled},page,n)==0 && n[0]>=40 && page[0]==1 && page[8]==0);
                check(f.permissionReport({legacy},page,n)==95 && n[0]>=40 && page[0]==0);
                page[0]=85; n[0]=123;
                check(f.permissionReport({unknown},page,n)==95 && n[0]==123 && page[0]==85);
                byte[] small=new byte[]{{85}};
                check(f.permissionReport({exact},small,n)==90 && n[0]>40 && small[0]==85);
                n[0]=123;
                check(f.moduleDescribe({wrong},page,n)==13 && n[0]==123 && page[0]==85);
                check(f.vmDescribe({wrong},page,n)==13 && n[0]==123 && page[0]==85);
            }}
        }}"""
    return f"""@file:JvmName("Observe")
        package example
        import wros.scene.Calls
        fun checkOk(ok:Boolean) {{ if(!ok) throw AssertionError() }}
        fun main(args:Array<String>) {{
            val f=Calls(128,65536); val page=ByteArray(65536); val n=LongArray(1)
            checkOk(f.permissionReport({exact},page,n)==0 && n[0]>40 && page[0].toInt()==1 && page[8].toInt()==1 && page[24].toInt()==1)
            checkOk(f.permissionReport({disabled},page,n)==0 && n[0]>=40 && page[0].toInt()==1 && page[8].toInt()==0)
            checkOk(f.permissionReport({legacy},page,n)==95 && n[0]>=40 && page[0].toInt()==0)
            page[0]=85; n[0]=123
            checkOk(f.permissionReport({unknown},page,n)==95 && n[0]==123L && page[0].toInt()==85)
            val small=byteArrayOf(85)
            checkOk(f.permissionReport({exact},small,n)==90 && n[0]>40 && small[0].toInt()==85)
            n[0]=123
            checkOk(f.moduleDescribe({wrong},page,n)==13 && n[0]==123L && page[0].toInt()==85)
            checkOk(f.vmDescribe({wrong},page,n)==13 && n[0]==123L && page[0].toInt()==85)
        }}"""



def private_submission(java):
    if java:
        return """package example; import wros.scene.Calls;
        final class Submission {
            public static void main(String[] args) {
                Calls f=new Calls(64,128);
                byte[] alias={101,120,99,104,97,110,103,101}, request=new byte[24], reply=new byte[128];
                long[] count={123}; request[8]=8; request[16]=42; reply[0]=85;
                if(f.capabilityOpen(alias)!=0 || f.moduleCallSubmit(request,reply,count)!=95 ||
                   request[16]!=42 || reply[0]!=85 || count[0]!=123 || f.capabilityClose()!=0)
                    throw new AssertionError();
            }
        }"""
    return """@file:JvmName("Submission")
        package example
        import wros.scene.Calls
        fun main(args:Array<String>) {
            val f=Calls(64,128)
            val alias=byteArrayOf(101,120,99,104,97,110,103,101)
            val request=ByteArray(24); val reply=ByteArray(128); val count=longArrayOf(123)
            request[8]=8; request[16]=42; reply[0]=85
            if(f.capabilityOpen(alias)!=0 || f.moduleCallSubmit(request,reply,count)!=95 ||
               request[16].toInt()!=42 || reply[0].toInt()!=85 || count[0]!=123L || f.capabilityClose()!=0)
                throw AssertionError()
        }"""


def exports(data):
    for start,_,_,body in sections(data):
        if data[start]==7:
            result=[(body.name(),body.byte(),body.uint()) for _ in range(body.count())]
            body.end()
            return result
    raise ValueError("missing export section")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain","sysroots","vm","bundle","output"):
        parser.add_argument("--"+name,required=True,type=Path)
    parser.add_argument("--sdk",type=Path,default=ROOT)
    parser.add_argument("--install-commit",help="select the synchronous-aot component from this commit of --sdk")
    parser.add_argument("--platform",default="unitree")
    parser.add_argument("--xmake",type=Path,help="build the checked message example from an installed Xmake selection")
    parser.add_argument("--language",choices=("java","kotlin"),required=True)
    parser.add_argument("--hidden-matrix",action="store_true",help="hide every imported operation individually")
    opts=parser.parse_args()
    out=opts.output.resolve();out.mkdir(exist_ok=False)
    group=cgroup_record();assert int(group["memory_max"])==68719476736 and int(group["swap_max"])==0
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.environ["TMPDIR"]=str(out)
    sdk=opts.sdk.resolve(); java=opts.language=="java"; ext="java" if java else "kt"
    if opts.install_commit:
        source=Source(opts.install_commit,sdk)
        installed=install(source,opts.platform,opts.language,out/"install",["--component","synchronous-aot"])
        sdk=Path(installed["directory"])
    names=[item["name"] for item in json.loads((sdk/"share/abi/ros.json").read_text())["operations"]]
    assert len(names)==len(set(names))
    cli=[sys.executable,sdk/"bin"/("wrjava" if java else "wrkt"),"--toolchain",opts.toolchain.resolve(),
         "--sysroots",opts.sysroots.resolve(),"--bundle",opts.bundle.resolve(),"--legacy-mte"]
    options=lambda selected:[part for name in selected for part in ("--ros-operation",name)]
    report={"complete":False,"cgroup":group,"commit":opts.install_commit,"sdk":str(sdk),"cases":[],"catalogue":names,"imports":{}}
    def save(): (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    def run(name,args,diagnostic=None,env=None,cwd=None):
        p=subprocess.run(list(map(str,args)),cwd=cwd or out,capture_output=True,timeout=300,env=env)
        text=p.stdout+p.stderr
        passed=p.returncode==0 if diagnostic is None else p.returncode!=0 and diagnostic in text
        if not name.startswith("hidden-") or not passed:(out/(name+".log")).write_bytes(text)
        report["cases"].append({"name":name,"status":p.returncode,"passed":passed}); save()
        if not passed:raise RuntimeError(name+" "+text[-2000:].decode(errors="replace"))
    def check_imports(path,expected):
        data=path.read_bytes()
        assert [(name,kind) for name,kind,_ in exports(data)]==[("_start",0)]
        assert keep_private_memory(data,{"_start"},max_pages=4096)==data
        actual={(r["module"],r["name"]) for r in inspect(data)}
        if actual!={("uwvm_ros_v2",n) for n in expected}:raise ValueError(f"unexpected linked imports: {actual}")
        report["imports"][path.name]=sorted(n for m,n in actual);save()
    def vm(engine,settings):
        args=[opts.vm.resolve(),*Profile().uwvm_feature_flags(),"--debug-fault-action","exit","--runtime-"+engine,
              "--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable","--wasm-set-main-module-name","main",
              "--ros-scene-create","robot","--ros-scene-bind","robot","main"]
        for operation,policy in settings:args+=["--ros-scene-interface","robot",operation,policy]
        return args
    catalog=out/("Catalog."+ext);catalog.write_text(entire_catalog(java,names))
    full=out/"catalog.wasm"
    run("compile-catalog",[*cli,"--main-class","example.Catalog",*options(names),catalog,"-o",full])
    check_imports(full,names)
    exchange=sdk/"examples"/opts.language/"synchronous-aot"/("Exchange."+ext)
    narrow=out/"guard.wasm"
    base=[*cli,"--main-class","example.Exchange",exchange,"-o",narrow]
    work=out/"guard-build"
    run("compile-guard",[*base,*options(GUARD),"--work",work])
    check_imports(narrow,GUARD)
    # Replay just the producer's Wasm compilation, inserting an observer around the
    # original wipe. Each observed range is read through volatile bytes after it returns.
    cmd=next(row["argv"] for row in json.loads((work/"results.json").read_text())["steps"] if row["name"]=="wasm")
    raw=out/"original-link"/"application.wasm"
    raw.parent.mkdir()
    env=dict(compiler_environment(opts.toolchain.resolve()),TMPDIR=str(work/"tmp"))
    original=cmd.copy();original[original.index("-o")+1]=str(raw)
    run("replay-unmodified-link",original,env=env,cwd=work)
    linked=raw.read_bytes()
    published=narrow.read_bytes()
    def unchanged_sections(data):
        return [data[a:b] for a,b,_,_ in sections(data) if data[a]!=7]
    assert unchanged_sections(linked)==unchanged_sections(published)
    assert set(exports(linked))=={("memory",2,0),*exports(published)}
    assert keep_private_memory(linked,{"_start"},max_pages=4096)==published
    receipt=json.loads((work/"results.json").read_text())
    assert receipt["linked_sha256"]==hashlib.sha256(linked).hexdigest()
    assert receipt["guest_sha256"]==hashlib.sha256(published).hexdigest()
    assert (work/"application.wasm").read_bytes()==published
    report["heap"]={"linked_exports":exports(linked),"published_exports":exports(published),
                    "other_sections_byte_identical":True,"linked_sha256":receipt["linked_sha256"],
                    "published_sha256":receipt["guest_sha256"]}
    guest_c=sdk/"language/jvm/guest.c"
    observer=out/"observe-wipe.c"
    observer.write_text("""static unsigned wipes, six, seven, nonzero;
static void observe_wipe(uint64_t address,int32_t count){
    volatile unsigned char *p=(volatile unsigned char *)(uintptr_t)address;
    unsigned present=0;
    for(int32_t i=0;i<count;i++) present |= p[i];
    wros_jvm_clear(address,count);
    for(int32_t i=0;i<count;i++) if(p[i]) __builtin_trap();
    wipes++; if(present){nonzero++; if(count==6)six++; if(count==7)seven++;}
}
#define wros_jvm_clear observe_wipe
#define _start probe_application_start
#include """+json.dumps(str(guest_c))+"""
#undef _start
void _start(void){
    probe_application_start();
    if(wipes!=14 || six!=1 || seven!=1 || nonzero<7) __builtin_trap();
}
""")
    probed=out/"observe-wipe.wasm"
    cmd[cmd.index(str(guest_c))]=str(observer)
    cmd[cmd.index("-o")+1]=str(probed)
    run("compile-wipe-observer",cmd,env=dict(compiler_environment(opts.toolchain.resolve()),TMPDIR=str(out)))
    probed.write_bytes(keep_private_memory(probed.read_bytes(),{"_start"},max_pages=4096))
    check_imports(probed,GUARD)
    expected=hashlib.sha256(narrow.read_bytes()).hexdigest()
    run("unknown-operation",[*base,*options(("unknown.operation",))],b"unknown ROS operation")
    run("duplicate-operation",[*base,*options(("abi","abi"))],b"duplicate ROS operation")
    run("method-not-selected",[*base,*options(GUARD[:-1])],b"guardTake")
    typed=sdk/"examples"/opts.language/"synchronous-aot"/("GuardApplication."+ext)
    run("typed-call-outside-selection",[*cli,"--main-class","example.GuardApplication",typed,"-o",narrow,
        *options(("abi",))],b"unexpected host import")
    assert hashlib.sha256(narrow.read_bytes()).hexdigest()==expected
    grants=["--ros-scene-grant","robot","signal","guard","signal","local","guard.create,guard.trigger,guard.take",
            "--ros-scene-grant","robot","limited","guard","limited","local","guard.create"]
    reports=("permission.report","module.describe","vm.describe")
    querysource=out/("Observe."+ext); querysource.write_text(observation(java))
    observer=out/"permission.wasm"
    run("compile-observer",[*cli,"--main-class","example.Observe",*options(reports),querysource,"-o",observer])
    check_imports(observer,reports)
    submit_ops=("capability.open","module.call.submit","capability.close")
    source=out/("Submission."+ext);source.write_text(private_submission(java))
    submission=out/"submission.wasm"
    run("compile-private-submission",[*cli,"--main-class","example.Submission",*options(submit_ops),source,"-o",submission])
    check_imports(submission,submit_ops)
    # An empty core module is enough: attachment and memory are checked before dispatch to a worker.
    worker=out/"worker.wasm";worker.write_bytes(b"\0asm\1\0\0\0")
    registered=["--ros-scene-bind","robot","worker","--ros-scene-call-budget","robot","65536","1",
                "--ros-scene-call","robot","solver","main","worker","solve","request-octets","response-octets",
                "64","64","2","10000000000","--ros-scene-grant","robot","exchange","module.call","solver",
                "registered-message","module.call.submit","--wasm-preload-library",worker,"worker"]
    if opts.xmake:
        project=out/"project"; project.mkdir()
        shutil.copyfile(exchange,project/exchange.name)
        sample=(sdk/"examples"/opts.language/"synchronous-aot/xmake.lua").read_text()
        sample=sample.replace('add_files("Main.'+ext+'")','add_files("Exchange.'+ext+'")')
        sample=sample.replace('set_wros_jvm_main("example.Main")','set_wros_jvm_main("example.Exchange")\n    add_wros_operations('+','.join(json.dumps(n) for n in GUARD)+')')
        (project/"xmake.lua").write_text(sample)
        env=dict(os.environ,UWVM_ROS_SDK_ROOT=str(sdk),WROS_PLATFORM=opts.platform,
                 WROS_TOOLCHAIN=str(opts.toolchain.resolve()),WROS_SYSROOTS=str(opts.sysroots.resolve()),
                 WROS_JVM_BUNDLE=str(opts.bundle.resolve()),XMAKE_GLOBALDIR=str(out/"xmake-settings"))
        xmake=str(opts.xmake.resolve())
        run("xmake-configure",[xmake,"f","-c","-y","-a","wasm32"],env=env,cwd=project)
        run("xmake-build",[xmake,"-j1","robot"],env=env,cwd=project)
        xguest=next(project.glob("build/*/wasm32/*/robot.wasm"))
        check_imports(xguest,GUARD)
        run("xmake-message-application",[*vm("int",[(n,"allow") for n in GUARD]),*grants,"--run",xguest])
    for engine in ("int","aot"):
        run(engine+"-granted-route-rejects-private-heap",[*vm(engine,[(n,"allow") for n in submit_ops]),*registered,"--run",submission])
        # The bound caller defaults to readable self policy. Visible peer/VM queries still need grants.
        run(engine+"-self-and-foreign-reports",[*vm(engine,[(n,"allow") for n in reports[1:]]),"--run",observer])
        run(engine+"-deny-catalog",[*vm(engine,[(n,"deny") for n in names]),"--run",full])
        allow=vm(engine,[(n,"allow") for n in GUARD])
        run(engine+"-no-grant",[*allow,"--run",narrow],b"unreachable")
        run(engine+"-resource",[*allow,*grants,"--run",narrow])
        run(engine+"-wiped-private-buffers",[*allow,*grants,"--run",probed])
        blocked=vm(engine,[(n,"deny" if n=="guard.trigger" else "allow") for n in GUARD])
        run(engine+"-operation-denied",[*blocked,*grants,"--run",narrow],b"unreachable")
    if opts.hidden_matrix:
        for hidden in names:
            settings=[(n,"hidden" if n==hidden else "deny") for n in names]
            run("hidden-"+hidden,[*vm("int",settings),"--run",full],b"ROS scene interface is hidden")
    report["complete"]=True;save()
    print(opts.language,len(names),"catalogue operations;",len(report["cases"]),"checks",flush=True)


if __name__=="__main__":
    main()
