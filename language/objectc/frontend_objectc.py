"""Compile GNUstep Objective-C sources into a closed u2ros WebAssembly module."""
import argparse
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
import artifacts
from compiler import compiler_environment, make_command
from frontend import audit
import qualification
import runtime

def main():
    parser = argparse.ArgumentParser(prog="wrobjc", description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("-o","--output",type=Path,required=True)
    parser.add_argument("--toolchain",type=Path)
    parser.add_argument("--sysroots",type=Path,action="append")
    parser.add_argument("--objc-clang",type=Path,default=os.environ.get("WROS_OBJC_CLANG"))
    parser.add_argument("--objc-runtime",type=Path,default=os.environ.get("WROS_OBJC_RUNTIME"))
    parser.add_argument("--target",choices=("wasm32","wasm64"))
    parser.add_argument("--core",choices=("3.0",),default="3.0")
    parser.add_argument("--eh",action=argparse.BooleanOptionalAction)
    qualification.arguments(parser)
    parser.add_argument("-O",choices=tuple("0123sz"))
    parser.add_argument("-g",action="store_true",default=None)
    parser.add_argument("-c",action="store_true",dest="compile_only")
    parser.add_argument("--reactor",action="store_true")
    parser.add_argument("--export",action="append",default=[])
    parser.add_argument("--std",choices=("c11","c17","c23","gnu11","gnu17","gnu23"))
    parser.add_argument("-I",dest="includes",action="append",default=[],type=Path)
    parser.add_argument("-D",dest="macros",action="append",default=[])
    opts=parser.parse_args()
    try:
        opts.threads = False
        if opts.O is None and opts.toolchain is not None and opts.sysroots is not None:
            opts.O = "3"
        profile, selected = qualification.frontend_profile(opts, "objectc")
        tc=opts.toolchain.resolve(strict=True)
        tools,rec=make_command(tc,opts.sysroots,profile,"c",["-c"],verify=True)
        extras = runtime.verified_inputs(tc, profile, rec, opts.objc_clang, opts.objc_runtime)
        objc = extras["objc_frontend"]
        lib = extras["objc_archive"].parent
        admit = qualification.admit("objectc", opts, profile, extras, selected_release=selected)
        sources=[s.resolve(strict=True) for s in opts.sources]
        if any(s.suffix not in (".m",".a",".o") for s in sources) or len(sources)>artifacts.MAX_MEMBERS:
            raise ValueError("expected Objective-C .m sources or checked WROS .o/.a objects")
        if opts.output.resolve() in sources:raise ValueError("output aliases an input")
        if opts.compile_only and (len(sources)!=1 or sources[0].suffix!='.m' or opts.export or opts.reactor):
            raise ValueError("-c requires one .m source without link options")
        if any(not re.fullmatch(r"[A-Za-z_]\w*",name,re.ASCII) for name in opts.export):
            raise ValueError("invalid Wasm export name")
        if any(not re.fullmatch(r"[A-Za-z_]\w*(?:=[^\r\n\x00]*)?",macro,re.ASCII) for macro in opts.macros):
            raise ValueError("invalid preprocessor definition")
        if any(not d.is_dir() for d in opts.includes):raise ValueError("include path is not a directory")
        flags=["-O"+opts.O,*(["-g"] if opts.g else []),"-I"+str(lib/"include"),"-I"+str(ROOT/"include"),
               *["-I"+str(d.resolve()) for d in opts.includes],*["-D"+m for m in opts.macros]]
        if opts.std:flags+=["-std="+opts.std]
        env=compiler_environment(tc)
        with tempfile.TemporaryDirectory(dir=opts.output.parent) as tmp:
            work=Path(tmp).resolve()
            # Authenticate the exact external objects before stripping SDK notes or linking them.
            inputs=artifacts.stage_inputs(sources,work,profile.to_dict(),rec["compiler_sha256"],
                                         rec["closure_sha256"],tc,qualification.object_releases(admit))
            objects=[]
            for i,source in enumerate(inputs):
                if source.suffix!='.m':
                    objects.append(source)
                    continue
                obj=work/f"objc-{i}.o"
                subprocess.run([objc,*tools[1:],*flags,*runtime.FLAGS,source,"-o",obj],check=True,env=env)
                objects.append(obj)
            if opts.compile_only:
                result=objects[0]
                data=artifacts.seal_object(artifacts.read_bounded(result),profile.to_dict(),rec["compiler_sha256"],
                                           rec["closure_sha256"],admit.get("release_sha256"))
            else:
                result=work/"module.wasm"
                linkflags=["-O"+opts.O,*(["-g"] if opts.g else [])]
                if opts.reactor:linkflags+=["-nostartfiles","-Wl,--no-entry"]
                linkflags+=["-Wl,--export="+name for name in opts.export]
                link,_=make_command(tc,opts.sysroots,profile,"cpp",linkflags,verify=True)
                if "-lunwind" in link:link.remove("-lunwind")
                link.extend([*objects,lib/"libobjc.a","-lc-printscan-long-double"])
                if opts.eh:link.append("-lunwind")
                subprocess.run([*link,"-o",result],check=True,env=env)
                data=artifacts.strip_notes(artifacts.read_bounded(result))
                audit(data,profile)
            result.write_bytes(data)
            qualification.finish(admit,opts,result,opts.output)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    return 0
