"""Build a ROS ABI query using an installed signed site and run both VM engines."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from separate_compilation import Profile, cgroup_record, inspect, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'vm', 'xmake', 'output'):
        parser.add_argument('--' + name, type=lambda text: Path(text).absolute(), required=True)
    args = parser.parse_args()
    sdk = args.sdk
    language = sdk.parent.name
    platform = sdk.parent.parent.name
    if sdk.name != 'development' or language not in ('c', 'cpp', 'fortran', 'lua', 'nim'):
        parser.error('supply one installed development selection')
    out = args.output
    state = dict(complete=False, cgroup=cgroup_record(), language=language, platform=platform,
                 sdk=str(sdk), vm=sha(args.vm), site=sha(sdk/'share/qualification/site-profile.json'), steps=[])
    out.mkdir(parents=True, exist_ok=False)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('WROS_', 'UWVM_', 'XMAKE_'))}
    env.update(PATH='/usr/bin:/bin', UWVM_ROS_SDK_ROOT=str(sdk), XMAKE_GLOBALDIR=str(out/'global'), TMPDIR=str(out),
               PYTHONDONTWRITEBYTECODE='1')

    def save():
        (out/'results.json').write_text(json.dumps(state, indent=2)+'\n')

    def run(name, argv, denial=None):
        log = out/(name+'.log')
        with log.open('xb') as stream:
            result = subprocess.run(list(map(str, argv)), cwd=out, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=420)
        state['steps'].append(dict(name=name, exit=result.returncode, log=sha(log)))
        save()
        if denial is None:
            result.check_returncode()
        elif result.returncode == 0 or denial not in log.read_text(errors='replace'):
            raise ValueError('missing expected refusal for '+name)

    script = ['includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))']
    def target(name, kind, file):
        script.extend([f'target("{name}")', f'set_kind("{kind}")', f'set_language("{language}")',
                       f'set_ros_platform("{platform}")', f'add_files("{file}")'])
    if language in ('c','cpp'):
        ext = 'c' if language=='c' else 'cpp'
        linkage = '' if language=='c' else 'extern "C" '
        (out/('query.'+ext)).write_text('#include <wros/scene.h>\n'+linkage+'int query(void) { return wr_abi(); }\n')
        (out/('app.'+ext)).write_text(linkage+'int query(void);\n'+linkage+
                                     'void _start(void) { if(query() != 2) __builtin_trap(); }\n')
        target('status', 'static', 'query.'+ext)
        script.append('target_end()')
        target('robot', 'binary', 'app.'+ext)
        script.extend(['add_deps("status")', 'set_wros_profile({build_receipt = true})'])
    elif language == 'nim':
        shutil.copyfile(sdk/'examples/nim/body.nim', out/'body.nim')
        target('robot','binary','body.nim')
        script.append('set_wros_profile({build_receipt = true})')
    elif language == 'fortran':
        shutil.copyfile(sdk/'examples/fortran/body.f90',out/'body.f90')
        target('robot','binary','body.f90')
        script.append('set_wros_profile({build_receipt = true})')
    else:
        (out/'body.lua').write_text('local x={1,2,3}; assert(x[2]==2 and wros.abi()==2)\n')
        target('robot','binary','body.lua')
        script.append('set_wros_profile({build_receipt = true, lua_abi = true, lua_seed = "7"})')
    script.append('target_end()')
    (out/'xmake.lua').write_text('\n'.join(script)+'\n')
    save()
    run('configure',[args.xmake,'f','-p','wasm-wasip1','-a','wasm32','-y'])
    run('build',[args.xmake,'-v','robot'])
    wasm, = (out/'build').rglob('robot.wasm')
    receipt = Path(str(wasm)+'.wros-build.json')
    evidence = json.loads(receipt.read_bytes())
    if evidence['mode']!='strict' or evidence['vm_sha256']!=state['vm']:
        raise ValueError('expected a strict build for the supplied VM')
    imports = inspect(wasm.read_bytes())
    if [(i['module'],i['name']) for i in imports] != [('uwvm_ros_v2','abi')]:
        raise ValueError('unexpected application imports')
    run('verify',[sys.executable,'-B',sdk/'install/qualification.py','--artifact',wasm,
                  '--vm',args.vm,'--receipt',receipt,'--approved-receipt-sha256',sha(receipt)])
    for engine in ('int','aot'):
        vm = [args.vm,*Profile(32).uwvm_feature_flags(),'--runtime-'+engine,'--runtime-compile-threads','0',
              '--runtime-llvm-jit-cache-path','disable','--wasm-set-main-module-name','main',
              '--ros-scene-create','robot','--ros-scene-bind','robot','main']
        run(engine+'-denied',[*vm,'--run',wasm],'scene interface is hidden')
        run(engine+'-allowed',[*vm,'--ros-scene-interface','robot','abi','allow','--run',wasm])
    state.update(complete=True, wasm=sha(wasm), receipt=sha(receipt), release=evidence['release_sha256'])
    save()


if __name__ == '__main__':
    main()
