"""Run a JVM model client on a mutually authenticated external matrix provider."""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import socket
import struct
import subprocess
import sys
import time
from separate_compilation import cgroup_record

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"install"))
from bootstrap import Source,install
from guest_profile import Profile
from imports import inspect

OPS=("capability.open","clock.create","clock.read","model.open","model.submit","model.take",
     "buffer.create","buffer.write","buffer.seal","request.describe","request.release")


def guest(java,fx,success,request_ns):
    def literal(data):
        ns=",".join(str(n if n<128 else n-256) for n in data)
        return "new byte[]{"+ns+"}" if java else "byteArrayOf("+ns+")"
    values=struct.pack("<2d",5.,6.)
    inference=fx.u64(0)+fx.u64(1)+fx.u64(0)+fx.profile("matrix.multiply")
    inference+=fx.text("mode")+fx.text("bytes")+fx.blob(fx.u64(1))+fx.u64(1)
    refat=len(inference)
    inference+=bytes(48)+fx.u64(32)+fx.u64(2)+fx.u64(8192)+fx.u64(0)
    expected=fx.text("succeeded" if success else "outcome_unknown")
    header="""package example; import wros.scene.Calls; final class Model {
      static void ck(boolean value){if(!value)throw new AssertionError();}
      static void put(byte[] a,int n,long v){for(int i=0;i<8;i++)a[n+i]=(byte)(v>>>(i*8));}
      static long get(byte[] a,int n){long v=0;for(int i=0;i<8;i++)v|=((long)a[n+i]&255L)<<(i*8);return v;}
      static boolean matches(byte[] a,int n,byte[] b){for(int i=0;i<b.length;i++)if(a[n+i]!=b[i])return false;return true;}
      public static void main(String[] args){
        Calls brain=new Calls(1024,1024), data=new Calls(1024,1024), clock=new Calls(1024,1024);
        byte[] out=new byte[1024],empty=new byte[0],word=new byte[8],pair=new byte[16];long[] n={0};
    """ if java else '''@file:JvmName("Model")
      package example
      import wros.scene.Calls
      private fun ck(v:Boolean){if(!v)throw AssertionError()}
      private fun put(a:ByteArray,n:Int,v:Long){for(i in 0..7)a[n+i]=(v ushr (8*i)).toByte()}
      private fun get(a:ByteArray,n:Int):Long{var v=0L;for(i in 0..7)v=v or ((a[n+i].toLong() and 255L) shl (8*i));return v}
      private fun matches(a:ByteArray,n:Int,b:ByteArray):Boolean{for(i in b.indices)if(a[n+i]!=b[i])return false;return true}
      fun main(args:Array<String>){
        val brain=Calls(1024,1024);val data=Calls(1024,1024);val clock=Calls(1024,1024)
        val out=ByteArray(1024);val empty=ByteArray(0);val word=ByteArray(8);val pair=ByteArray(16);val n=longArrayOf(0)
    '''
    body="""
      ck(brain.capabilityOpen(@brain)==0 && data.capabilityOpen(@data)==0 && clock.capabilityOpen(@steady)==0);
      ck(clock.clockCreate(word,out,n)==0); LONG clockId=get(out,0);
      ck(brain.modelOpen(@model,out,n)==0); LONG session=get(out,0);
      ck(data.bufferCreate(@layout,out,n)==0); LONG id=get(out,0);
      BYTES write=@write; put(write,0,id);ck(data.bufferWrite(write,out,n)==0);
      BYTES seal=@seal; put(seal,0,id);ck(data.bufferSeal(seal,out,n)==0);
      put(word,0,clockId);ck(clock.clockRead(word,out,n)==0);LONG deadline=get(out,0)+@duration;
      BYTES request=@body;put(request,0,session);put(request,16,session);put(request,@handle,id);put(request,@deadline,deadline);
      ck(brain.modelSubmit(request,out,n,SOURCES)==0 && get(request,@slot)==0L);
      LONG job=get(out,0);put(word,0,job);BYTES wanted=@state;BYTES now=@zero;put(now,0,clockId);
      while(true){
        ck(brain.requestDescribe(word,out,n)==0);
        if(matches(out,8,wanted))break;
        ck(clock.clockRead(now,out,n)==0 && get(out,0)<deadline+1000000000L);
      }
    """
    if success:
        body+="""
        put(pair,0,session);put(pair,8,job);ck(brain.modelTake(pair,out,n)==0 && n[0]>=16L);
        ck(matches(out,LENGTH-16,@result));ck(brain.requestRelease(word,out,n)==0 && get(out,0)==1L);
        """
    else:body+="ck(brain.requestRelease(word,out,n)==11);"
    # Keep the import visible in the fault profile without submitting more work.
    if not success:body+="ck(brain.modelTake(pair,out,n)!=0);"
    replacements={"@brain":literal(b"brain"),"@data":literal(b"data"),"@steady":literal(b"steady"),
      "@model":literal(fx.profile("matrix.cpu")),"@layout":literal(fx.layout(identity="tensor",digest=fx.PROFILE_SHA,shape=(16,),size=16)),
      "@write":literal(bytes(16)+fx.blob(values)),"@seal":literal(bytes(8)+fx.blob(hashlib.sha256(values).digest())),
      "@body":literal(inference),"@slot":str(refat),"@handle":str(refat+8),"@deadline":str(len(inference)-8),
      "@duration":str(request_ns)+"L","@state":literal(expected),"@zero":literal(bytes(8)),"@result":literal(struct.pack("<2d",17.,39.)),
      "LENGTH":"(int)n[0]" if java else "n[0].toInt()",
      "LONG":"long" if java else "val","BYTES":"byte[]" if java else "val","SOURCES":"new Calls[]{data}" if java else "arrayOf(data)"}
    for name,value in replacements.items():body=body.replace(name,value)
    return header+body+("}}" if java else "}")


def run_vm(fx,issue,o,guest,mode,engine,out,report):
    label=mode+"-"+engine
    with ExitStack() as owner,(out/(label+".peer.log")).open("wb") as peerlog:
        left,right=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
        for s in (left,right):
            owner.callback(s.close);s.setsockopt(socket.SOL_SOCKET,socket.SO_PASSCRED,1)
        client_key,peer_key=issue(owner)
        read,write=os.pipe2(os.O_CLOEXEC)
        for fd in (read,write):owner.callback(os.close,fd)
        peer=subprocess.Popen([sys.executable,fx.__file__,"--receiver-fd",str(right.fileno()),"--mode",mode,
             "--transport-library",str(o.transport_library.resolve()),"--pid-fd",str(read),"--key-fd",str(peer_key)],
             pass_fds=(right.fileno(),read,peer_key),stdout=peerlog,stderr=peerlog)
        right.close()
        try:
            clock=os.open(f"/proc/{peer.pid}/ns/time",os.O_RDONLY|os.O_CLOEXEC);owner.callback(os.close,clock)
            args=fx.flags(left.fileno(),peer.pid,time.monotonic_ns()+20000000000)
            i=args.index("--ros-scene-model-kernel-channel");args[i]="--ros-scene-model-channel"
            args[i+19:i+19]=[str(client_key),str(clock)]
            vm=subprocess.Popen([o.vm,*Profile().uwvm_feature_flags(),"--debug-fault-action","exit","--wasm-set-main-module-name","main",
                "--runtime-"+engine,"--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable",*args,"--run",guest],
                pass_fds=(left.fileno(),client_key,clock),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                assert os.write(write,struct.pack("=I",vm.pid))==4
                stdout,stderr=vm.communicate(timeout=30)
            finally:
                if vm.poll() is None:vm.kill();vm.wait()
            (out/(label+".log")).write_bytes(stdout+stderr)
            alive=peer.poll() is None
            report["cases"].append(dict(name=label,vm_status=vm.returncode,peer_alive_at_vm_exit=alive,peer_status=peer.poll()))
            (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
            assert vm.returncode==0,stderr[-1500:]
            if mode=="crash":assert peer.wait(timeout=3)==-signal.SIGSEGV
            else:assert alive
        finally:
            if peer.poll() is None:peer.terminate()
            peer.wait(timeout=5)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("sdk","vm-source","toolchain","sysroots","bundle","vm","output","transport-library"):p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--commit",required=True);p.add_argument("--language",choices=("java","kotlin"),required=True)
    o=p.parse_args();cg=cgroup_record();assert int(cg["memory_max"])==68719476736 and int(cg["swap_max"])==0
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    out=o.output.resolve();out.mkdir(exist_ok=False);os.environ["TMPDIR"]=str(out)
    sys.path.insert(0,str(o.vm_source.resolve()/"test/0084.ros-runtime"))
    import run_model_attachment_vm as fx
    from attachment_peer import issue
    sdk=Path(install(Source(o.commit,o.sdk.resolve()),"unitree",o.language,out/"install",["--component","synchronous-aot"])["directory"])
    report=dict(complete=False,commit=o.commit,cgroup=cg,cases=[],guest_digests={},
                vm_sha256=hashlib.sha256(o.vm.read_bytes()).hexdigest(),
                fixture_sha256=hashlib.sha256(Path(fx.__file__).read_bytes()).hexdigest(),transport_sha256=hashlib.sha256(o.transport_library.read_bytes()).hexdigest())
    java=o.language=="java"
    for name,modes,request_ns in (("success",("success",),4000000000),
                                  ("unknown",("crash","wrong-sequence"),4000000000),
                                  ("timeout",("timeout",),500000000)):
        app=out/("Model.java" if java else "Model.kt")
        app.write_text(guest(java,fx,name=="success",request_ns))
        artifact=out/(name+".wasm")
        result=subprocess.run([sys.executable,sdk/"bin"/("wrjava" if java else "wrkt"),"--legacy-mte","--toolchain",o.toolchain.resolve(),
           "--sysroots",o.sysroots.resolve(),"--bundle",o.bundle.resolve(),"--main-class","example.Model",
           *(s for n in OPS for s in ("--ros-operation",n)),app,"-o",artifact],cwd=out,capture_output=True,timeout=180)
        (out/(name+"-compile.log")).write_bytes(result.stdout+result.stderr)
        if result.returncode:raise ValueError(result.stderr[-1000:])
        assert {(i["module"],i["name"]) for i in inspect(artifact.read_bytes())}=={("uwvm_ros_v2",n) for n in OPS}
        report["guest_digests"][name]=hashlib.sha256(artifact.read_bytes()).hexdigest()
        for mode in modes:
            for engine in ("int","aot"):run_vm(fx,issue,o,artifact,mode,engine,out,report)
    report["complete"]=True;(out/"results.json").write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":main()
