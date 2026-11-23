"""Build the native Zig bitcode frontend and the LLVM IR storage pass."""
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def build_frontend(source, bootstrap, destination, work, jobs=2):
    work.mkdir(parents=True, exist_ok=True)
    temp = work / "tmp"
    temp.mkdir(exist_ok=True)
    environment = dict(os.environ, TMPDIR=str(temp), ZIG_GLOBAL_CACHE_DIR=str(work / "global"),
                       ZIG_LOCAL_CACHE_DIR=str(work / "local"))
    subprocess.run([bootstrap, "build", "--cache-dir", work / "local", "--global-cache-dir", work / "global",
                    "--prefix", work / "output", "-j" + str(jobs), "-Dtarget=x86_64-linux-musl",
                    "-Doptimize=ReleaseSmall", "-Dstrip=true", "-Dno-lib=true", "-Denable-llvm=false",
                    "-Duse-llvm=true", "-Ddev=wros", "-Dversion-string=0.16.0"],
                   check=True, cwd=source, env=environment)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / "output/bin/zig", destination)


def build_marker(source, config, cxx, destination, work):
    def flags(*args):
        return shlex.split(subprocess.check_output([config, *args], text=True))
    work.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([cxx, *flags("--cxxflags"), "-Os", "-g0", source, *flags("--ldflags"),
                    *flags("--libs", "core", "irreader", "bitwriter"), *flags("--system-libs"),
                    "-o", destination], check=True, cwd=work, env=dict(os.environ, TMPDIR=str(work)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    sub = parser.add_subparsers(dest="part", required=True)
    sub.add_parser("frontend").add_argument("--zig", type=Path, required=True)
    marker = sub.add_parser("marker")
    marker.add_argument("--llvm-config", type=Path, required=True)
    marker.add_argument("--cxx", default="c++")
    options = parser.parse_args()
    here = Path(__file__).resolve().parent
    if options.part == "frontend":
        build_frontend(here / "upstream", options.zig.resolve(strict=True),
                       options.dest.resolve(), options.work.resolve(), options.jobs)
    else:
        build_marker(here / "mark_mte.cpp", options.llvm_config.resolve(strict=True), options.cxx,
                     options.dest.resolve(), options.work.resolve())
