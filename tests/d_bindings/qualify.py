"""Compile an installed D binding with LDC BetterC and the SDK WasmMTE code generator."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT/'install'),str(ROOT/'language/fortran')]
from compiler import compiler_environment, make_command
from guest_profile import Profile
from imports import inspect
from prepare import require_marker


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('sdk','ldc','marker','toolchain','sysroots','vm','output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if '.tmp' not in out.parts: raise ValueError('choose an unused .tmp output')
    out.mkdir(parents=True,exist_ok=False)
    sdk,tc = args.sdk.resolve(strict=True),args.toolchain.resolve(strict=True)
    marker,ldc,vm = (p.resolve(strict=True) for p in (args.marker,args.ldc,args.vm))
    profile,env = Profile(32),compiler_environment(tc)
    require_marker(marker,tc)
    bindings = sdk/'language/d'
    inputs = (ldc, marker, tc/'bin/clang', vm, args.sysroots, HERE/'entry.c', HERE/'control.d',
              bindings/'imports.c', bindings/'wros_scene.d', sdk/'include/wros/scene.h')
    result = dict(complete=False,scope='wasm32 BetterC fixed-width bindings, nonthreaded finite array and ROS ABI query',
                  inputs={str(p):sha(p) for p in inputs},steps=[])
    def save():
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    def run(name,cmd,env=None,denied=False):
        argv=list(map(str,cmd))
        log=out/(name+'.log')
        with log.open('xb') as stream:
            status=subprocess.run(argv,cwd=out,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120)
        result['steps'].append(dict(name=name,argv=argv,exit=status.returncode))
        save()
        if denied:
            if status.returncode==0 or 'scene interface is hidden' not in log.read_text():
                raise ValueError('missing denied import')
        else:
            status.check_returncode()
    run('ldc',[ldc,'-mtriple=wasm32-unknown-wasip1','-betterC','-O0','-g','-c','-output-ll',
               '-I='+str(bindings),'-of='+str(out/'control.ll'),HERE/'control.d'])
    run('mark-llvm-ir',[marker,'32','on',out/'control.ll',out/'control.bc'],env)
    for stage, flags in [
        ('compile',['-O3','-g','-x','ir','-c',out/'control.bc','-o',out/'control.o']),
        ('link',['-O3','-g','-ffunction-sections','-I'+str(sdk/'include'),'-nostartfiles','-Wl,--no-entry',
                 '-Wl,--export=_start',HERE/'entry.c',bindings/'imports.c',out/'control.o','-o',out/'robot.wasm'])]:
        argv,identity = make_command(tc,[args.sysroots],profile,'c',list(map(str,flags)),verify=True)
        run(stage,argv,env)
    module=out/'robot.wasm'
    if inspect(module.read_bytes()) != [dict(module='uwvm_ros_v2',name='abi',kind=0,params=[],results=['i32'])]:
        raise ValueError('unexpected Wasm import surface')
    for engine in ('int','aot'):
        cmd=[vm,*profile.uwvm_feature_flags(),'--runtime-'+engine,'--runtime-compile-threads','0',
             '--runtime-llvm-jit-cache-path','disable','--wasm-set-main-module-name','main',
             '--ros-scene-create','robot','--ros-scene-bind','robot','main']
        run(engine+'-hidden',[*cmd,'--run',module],denied=True)
        run(engine+'-granted',[*cmd,'--ros-scene-interface','robot','abi','allow','--run',module])
    result.update(complete=True,wasm=sha(module),closure=identity['closure_sha256'])
    save()


if __name__ == '__main__':
    main()
