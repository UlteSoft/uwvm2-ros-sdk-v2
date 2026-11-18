#!/usr/bin/env python3
"""Prepare a static GNUstep Wasm runtime and its accompanying public headers."""
import argparse
import json
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from compiler import compiler_environment, make_command
from guest_profile import Profile
import runtime

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, required=True)
    parser.add_argument("--sysroots", type=Path, action="append", required=True)
    parser.add_argument("--objc-clang", type=Path)
    parser.add_argument("--target", choices=["wasm32", "wasm64"], default="wasm32")
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--eh", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if not 1 <= args.jobs <= 32: raise ValueError("--jobs must be between 1 and 32")
        profile = Profile(int(args.target[4:]), exceptions="eh" if args.eh else "noeh", mte=args.mte)
        base = args.toolchain.resolve(strict=True)
        objc = runtime.frontend(base, args.objc_clang)
        archive_dir = args.output.absolute()
        if archive_dir.exists(): raise ValueError("runtime output already exists")
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        env = compiler_environment(base)
        with tempfile.TemporaryDirectory(dir=archive_dir.parent) as temp:
            stage = Path(temp)
            def run(argv, cwd=stage):
                subprocess.run(list(map(str, argv)), check=True, cwd=cwd, env=env)
            runtime.vendor_inputs()
            source = stage / "libobjc2"
            robin = stage / "robin-map"
            runtime.extract("libobjc2-a21ae931.tar.gz", source)
            runtime.extract("robin-map-1.4.0.tar.gz", robin)
            run(["patch", "-F", "0", "--batch", "-p1", "-i", runtime.VENDOR / "libobjc2-wasm.patch"], source)
            build = stage / "build"
            out = stage / "output"
            includes = out / "include/objc"
            includes.mkdir(parents=True)
            config = {"CMAKE_SYSTEM_NAME": "Generic", "CMAKE_SYSTEM_PROCESSOR": args.target,
                      "CMAKE_BUILD_TYPE": "Release", "CMAKE_TRY_COMPILE_TARGET_TYPE": "STATIC_LIBRARY",
                      "CMAKE_AR": base/"bin/llvm-ar", "CMAKE_RANLIB":base/"bin/llvm-ranlib",
                      "WASM":"ON", "BUILD_STATIC_LIBOBJC":"ON", "BUILD_SHARED_LIBOBJC":"OFF",
                      "OLDABI_COMPAT":"OFF", "TESTS":"OFF", "FETCHCONTENT_FULLY_DISCONNECTED":"ON",
                      "FETCHCONTENT_SOURCE_DIR_ROBINMAP":robin}
            for kind, lang in (("C","c"),("CXX","cpp"),("OBJC","c"),("OBJCXX","cpp"),("ASM","c")):
                command, rec = make_command(base, args.sysroots, profile, lang, ["-c"], verify=True)
                flags = [*command[1:-1], "-ffunction-sections", "-fdata-sections", "-fno-exceptions"]
                compiler = Path(command[0])
                if kind in ("OBJC","OBJCXX"):
                    compiler = objc
                    flags.extend(runtime.FLAGS)
                config["CMAKE_"+kind+"_COMPILER"] = compiler
                config["CMAKE_"+kind+"_FLAGS"] = shlex.join(flags)
                config["CMAKE_"+kind+"_FLAGS_RELEASE"] = "-O3 -g"
            run(["cmake","-S",source,"-B",build,"-G","Ninja",*[f"-D{k}={v}" for k,v in config.items()]])
            run(["cmake","--build",build,"--target","objc-static","--parallel",args.jobs])
            shutil.copyfile(build/"libobjc.a", out/"libobjc.a")
            for h in (source/"objc").glob("*.h"): shutil.copyfile(h, includes/h.name)
            shutil.copyfile(build/"objc/objc-config.h", includes/"objc-config.h")
            cmd, rec = make_command(base, args.sysroots, profile, "c", ["-c"], verify=True)
            base_obj=stage/"base_object.o"
            run([objc,*cmd[1:],*runtime.FLAGS,"-O3","-g","-I"+str(out/"include"),
                 ROOT/"language/objectc/base_object.m","-o",base_obj])
            run([base/"bin/llvm-ar","rD",out/"libobjc.a",base_obj])
            witness=runtime.abi(profile,objc,rec)
            witness["files"]=runtime.public_files(out)
            (out/"runtime.json").write_text(json.dumps(witness,indent=2)+"\n")
            out.rename(archive_dir)
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")

if __name__ == "__main__": main()
