"""Execute an installed JVM guest on receive-only sensor descriptors and verify queue use externally."""
import argparse
import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import termios
from separate_compilation import cgroup_record

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"install"))
from bootstrap import Source,install
from guest_profile import Profile
from imports import inspect


def source(java,fixture):
    def literal(data):
        values=",".join(str(i if i<128 else i-256) for i in data)
        return "new byte[]{"+values+"}" if java else "byteArrayOf("+values+")"
    msg=fixture.text("sensor.frame")+fixture.text(fixture.TYPE)+fixture.text(fixture.ENCODING)+fixture.blob(fixture.PAYLOAD)
    data=fixture.blob(fixture.PAYLOAD)
    fields={"profile":fixture.PROFILE_WIRE,"sensor":b"sensor","denied":b"no-export","rate":b"rate","buffer":b"frames",
            "message":msg,"data":data,"suffix":fixture.text(fixture.SCHEMA)+fixture.blob(fixture.SCHEMA_SHA)+fixture.text(fixture.BUFFER)+fixture.blob(fixture.BUFFER_SHA)+fixture.text("logical")+fixture.text("count")+b"".join(fixture.u64(n) for n in (101,1,1))}
    if java:
        header="""package example; import wros.scene.Calls; final class Sensor {
        static void ck(boolean ok){if(!ok)throw new AssertionError();}
        static boolean matches(byte[] actual,int offset,byte[] expected) {
            for(int i=0;i<expected.length;++i)if(actual[offset+i]!=expected[i])return false;return true;
        }
        static long word(byte[] a,int n) {long v=0;for(int i=0;i<8;++i)v|=((long)a[n+i]&255L)<<(8*i);return v;}
        static byte[] words(long... a){byte[] v=new byte[a.length*8];for(int n=0;n<a.length;n++)for(int i=0;i<8;++i)v[8*n+i]=(byte)(a[n]>>>(8*i));return v;}
        public static void main(String[] args){
            Calls s=new Calls(1024,4096),d=new Calls(1024,4096),r=new Calls(1024,4096),b=new Calls(1024,4096);
            byte[] dst=new byte[4096],one={85},empty=new byte[0]; long[] n={99};
        """
    else:
        header='''@file:JvmName("Sensor")
        package example
        import wros.scene.Calls
        private fun ck(ok:Boolean){if(!ok)throw AssertionError()}
        private fun matches(actual:ByteArray,offset:Int,expected:ByteArray):Boolean {
            for(i in expected.indices)if(actual[offset+i]!=expected[i])return false
            return true
        }
        private fun word(a:ByteArray,n:Int):Long {var v=0L;for(i in 0..7)v=v or ((a[n+i].toLong() and 255L) shl (8*i));return v}
        private fun words(vararg a:Long):ByteArray {val v=ByteArray(8*a.size);for(n in a.indices)for(i in 0..7)v[8*n+i]=(a[n] ushr (8*i)).toByte();return v}
        fun main(args:Array<String>){
            val s=Calls(1024,4096);val d=Calls(1024,4096);val r=Calls(1024,4096);val b=Calls(1024,4096)
            val dst=ByteArray(4096);val one=byteArrayOf(85);val empty=ByteArray(0);val n=longArrayOf(99)
        '''
    content="""
        ck(s.capabilityOpen(SENSOR)==0 && d.capabilityOpen(DENIED)==0 && r.capabilityOpen(RATE)==0 && b.capabilityOpen(BUFFER)==0);
        ck(r.sensorOpen(PROFILE,dst,n)==11);
        ck(d.sensorOpen(PROFILE,dst,n)==0); DECL denied=word(dst,0);
        ck(d.sensorTake(words(denied),dst,n)==13);
        ck(s.sensorOpen(PROFILE,dst,n)==0 && n[0]==8L); DECL active=word(dst,0);
        ck(d.sensorDescribe(words(active),dst,n)==9);
        ck(s.sensorTake(words(active),one,n)==90 && n[0]>1L);
        ck(s.sensorTake(words(active),dst,n)==11);
        ck(s.sensorTake(words(active),dst,n)==0);
        ck(word(dst,0)==active && word(dst,8)==1L && word(dst,16)==1L && matches(dst,88,MESSAGE));
        DECL buffer=word(dst,AT); ck(buffer!=0L && matches(dst,AT+8,SUFFIX));
        ck(b.bufferRead(words(buffer,0,4),dst,n)==0 && n[0]==12L && matches(dst,0,DATA));
        ck(s.sensorTake(words(active),dst,n)==11);
        ck(s.sensorDescribe(words(active),dst,n)==0 && matches(dst,0,PROFILE));
        ck(b.resourceClose(words(buffer),empty,n)==0 && s.resourceClose(words(active),empty,n)==0);
        ck(s.sensorTake(words(active),dst,n)==9 && d.resourceClose(words(denied),empty,n)==0);
        ck(b.capabilityClose()==0 && d.capabilityClose()==0 && s.capabilityClose()==0 && r.capabilityClose()==0);
    """
    for key,v in fields.items():content=content.replace(key.upper(),literal(v))
    return header+content.replace("DECL","long" if java else "val").replace("AT",str(88+len(msg)))+("}}" if java else "}")


def main():
    import importlib
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ("sdk","vm-source","toolchain","sysroots","bundle","vm","output"):parser.add_argument("--"+n,type=Path,required=True)
    parser.add_argument("--commit",required=True)
    parser.add_argument("--language",choices=("java","kotlin"),required=True)
    o=parser.parse_args();group=cgroup_record(); assert int(group["memory_max"])==68719476736 and int(group["swap_max"])==0
    sys.path.insert(0,str(o.vm_source.resolve()/"test/0084.ros-runtime"))
    fixture=importlib.import_module("run_scene_sensors");out=o.output.resolve();out.mkdir(exist_ok=False)
    os.environ["TMPDIR"]=str(out)
    sdk=Path(install(Source(o.commit,o.sdk.resolve()),"unitree",o.language,out/"install",["--component","synchronous-aot"])["directory"])
    report={"commit":o.commit,"complete":False,"cgroup":group,"cases":[],"fixture_sha256":hashlib.sha256(Path(fixture.__file__).read_bytes()).hexdigest()}
    def save(): (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    def run(name,args,fds=()):
        proc=subprocess.run(list(map(str,args)),cwd=out,pass_fds=fds,capture_output=True,timeout=180)
        (out/(name+".log")).write_bytes(proc.stdout+proc.stderr)
        report["cases"].append({"name":name,"exit":proc.returncode});save()
        if proc.returncode:raise ValueError(name+" "+proc.stderr[-1200:].decode(errors="replace"))
    java=o.language=="java";app=out/("Sensor.java" if java else "Sensor.kt");app.write_text(source(java,fixture));guest=out/"Sensor.wasm"
    names=("capability.open","capability.close","sensor.open","sensor.describe","sensor.take","buffer.read","resource.close")
    run("compile",[sys.executable,sdk/"bin"/("wrjava" if java else "wrkt"),"--legacy-mte","--toolchain",o.toolchain.resolve(),
             "--sysroots",o.sysroots.resolve(),"--bundle",o.bundle.resolve(),"--main-class","example.Sensor",
             *(a for n in names for a in ("--ros-operation",n)),app,"-o",guest])
    assert {(r["module"],r["name"]) for r in inspect(guest.read_bytes())}=={("uwvm_ros_v2",n) for n in names}
    report["guest_sha256"]=hashlib.sha256(guest.read_bytes()).hexdigest()
    for engine in ("int","aot"):
        pipes=[]
        try:
            for _ in fixture.ALIASES:
                pair=os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC);pipes.append(pair)
                assert os.write(pair[1],fixture.PACKET)==len(fixture.PACKET)
            readers=tuple(pair[0] for pair in pipes)
            run(engine,[o.vm,*Profile().uwvm_feature_flags(),"--wasm-set-main-module-name","main","--debug-fault-action","exit","--runtime-"+engine,
                "--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable",*fixture.configured(readers),"--run",guest],readers)
            pending=[]
            for fd in readers:
                count=array.array('i',[0]);fcntl.ioctl(fd,termios.FIONREAD,count,True);pending.append(count[0])
            report["cases"][-1]["pending_bytes"]=pending;save()
            assert pending==[0,len(fixture.PACKET),len(fixture.PACKET)]
        finally:
            for pair in pipes:
                for fd in pair:os.close(fd)
    report["complete"]=True;save()

if __name__=="__main__":main()
