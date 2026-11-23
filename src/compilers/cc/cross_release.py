"""Cross-build the SDK's Linux C/C++ frontends and package them with the published Wasm sysroots."""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from rebuild import host_tools, write_json
from package_native import package


# The Debian i686 GCC triple and its glibc multiarch directory have different names.
HOSTS = {
    "linux-i686": ("i686-linux-gnu", "i386-linux-gnu", "i686", ["-march=i686"]),
    "linux-aarch64": ("aarch64-linux-gnu", "aarch64-linux-gnu", "aarch64", ["-march=armv8-a"]),
    "linux-arm": ("arm-linux-gnueabi", "arm-linux-gnueabi", "arm",
                  ["-march=armv5te", "-mfloat-abi=soft"]),
    "linux-armhf": ("arm-linux-gnueabihf", "arm-linux-gnueabihf", "armv7",
                    ["-march=armv7-a", "-mfloat-abi=hard", "-mfpu=vfpv3-d16"]),
}


def cross_options(args):
    triple, multiarch, processor, cpu = HOSTS[args.host]
    gcc = args.sysroot / "usr/lib/gcc" / triple
    installs = sorted(p for p in gcc.glob("*") if (p / "libgcc.a").is_file())
    if len(installs) != 1:
        raise ValueError(f"expected one target GCC development installation under {gcc}, found {installs}")
    gcc = installs[0]
    include = args.sysroot / "usr/include"
    common = include / "c++" / gcc.name
    specific = include / multiarch / "c++" / gcc.name
    for path in (common / "vector", specific / "bits/c++config.h",
                 args.sysroot / "usr/lib" / multiarch / "libc.a", gcc / "libstdc++.a"):
        if not path.is_file():
            raise ValueError("incomplete target development sysroot: " + str(path))
    for name in ("llvm-min-tblgen", "llvm-tblgen", "clang-tblgen", "llvm-ar", "llvm-ranlib"):
        if not os.access(args.native_tools / name, os.X_OK):
            raise ValueError("missing build-machine LLVM tool: " + str(args.native_tools / name))
    flags = [f"--gcc-install-dir={gcc}", *cpu]
    # Select the target libc and C++ headers even if the build machine has the same GCC major.
    cxx = [*flags, "-nostdinc++", "-isystem", str(common), "-isystem", str(specific),
           "-isystem", str(common / "backward")]
    options = {
        "CMAKE_SYSTEM_NAME": "Linux", "CMAKE_SYSTEM_PROCESSOR": processor, "CMAKE_SYSROOT": args.sysroot,
        "LLVM_HOST_TRIPLE": triple, "LLVM_NATIVE_TOOL_DIR": args.native_tools,
        "CMAKE_C_COMPILER_TARGET": triple, "CMAKE_CXX_COMPILER_TARGET": triple,
        "CMAKE_ASM_COMPILER": args.bootstrap / "bin/clang", "CMAKE_ASM_COMPILER_TARGET": triple,
        "CMAKE_C_FLAGS": shlex.join(flags), "CMAKE_CXX_FLAGS": shlex.join(cxx),
        "CMAKE_ASM_FLAGS": shlex.join(flags), "CMAKE_AR": args.native_tools / "llvm-ar",
        "CMAKE_RANLIB": args.native_tools / "llvm-ranlib",
        "CMAKE_EXE_LINKER_FLAGS": shlex.join([f"-fuse-ld={args.bootstrap}/bin/ld.lld", "-static", "-Wl,-s"]),
        "CMAKE_FIND_ROOT_PATH_MODE_PROGRAM": "NEVER", "CMAKE_FIND_ROOT_PATH_MODE_INCLUDE": "ONLY",
        "CMAKE_FIND_ROOT_PATH_MODE_LIBRARY": "ONLY", "CMAKE_FIND_ROOT_PATH_MODE_PACKAGE": "ONLY",
        "LLVM_ENABLE_Z3_SOLVER": "OFF", "LLVM_ENABLE_LIBPFM": "OFF",
        "CMAKE_DISABLE_PRECOMPILE_HEADERS": "ON",
    }
    if args.host == "linux-aarch64":
        options["CMAKE_PROJECT_TOP_LEVEL_INCLUDES"] = str(HERE / "aarch64-static-clang.cmake")
    if args.host == "linux-arm":
        # BLAKE3's C11 atomic load calls __atomic_load on ARMv5. LLVM's C++
        # atomics probe uses libstdc++ builtins and does not detect that symbol.
        atomic = gcc / "libatomic.a"
        if not atomic.is_file():
            raise ValueError("missing target static atomic runtime: " + str(atomic))
        options["CMAKE_CXX_STANDARD_LIBRARIES"] = shlex.quote(str(atomic))
    # The archives never leave the build directory. Store each object only once.
    for language in ("C", "CXX"):
        options[f"CMAKE_{language}_ARCHIVE_CREATE"] = "<CMAKE_AR> qcT <TARGET> <LINK_FLAGS> <OBJECTS>"
        options[f"CMAKE_{language}_ARCHIVE_APPEND"] = "<CMAKE_AR> qT <TARGET> <LINK_FLAGS> <OBJECTS>"
    return options


def publish(host, build, output):
    distribution = json.loads((HERE / "distribution/distribution.json").read_bytes())
    distribution["host"] = host
    distribution["sysroot_producer_sha256"] = distribution["programs"]["clang"]
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as scratch:
        stage = Path(scratch)
        packages = {}
        for name in ("clang", "wasm-ld", "llvm-ar"):
            temporary = stage / (name + ".tar.xz")
            entry = package(build / "bin" / name, name, temporary, host=host)
            filename = name + "-" + entry["compressed_sha256"][:20] + ".tar.xz"
            temporary.rename(stage / filename)
            entry.update(host=host, path=f"bin/packages/{host}/wrcc/{filename}")
            if host == "linux-armhf":
                entry["required_hwcap"] = ["vfp", "vfpv3"]
            packages[name] = entry
        distribution["programs"] = {name: entry["sha256"] for name, entry in packages.items()}
        distribution["programs"]["clang++"] = distribution["programs"]["clang"]
        write_json(stage / "cc-distribution.json", distribution)
        write_json(stage / "cc.json", {"schema": 1, "host": host, "packages": packages})
        for file in sorted(stage.glob("*.tar.xz")):
            os.replace(file, output / file.name)
        os.replace(stage / "cc-distribution.json", output / "cc-distribution.json")
        os.replace(stage / "cc.json", output / "cc.json")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--host", choices=HOSTS, required=True)
    cli.add_argument("--bootstrap", type=Path, required=True, help="build-machine Clang and LLD prefix")
    cli.add_argument("--native-tools", type=Path, required=True, help="bin directory with the SDK LLVM 23.1.5 TableGen tools")
    cli.add_argument("--sysroot", type=Path, required=True, help="Linux target sysroot including glibc and GCC development files")
    cli.add_argument("--work", type=Path, required=True, help="parent of the per-host Ninja build directories")
    cli.add_argument("--output", type=Path, required=True, help="output package root, with one subdirectory per host")
    cli.add_argument("--jobs", type=int, default=4)
    cli.add_argument("--cmake", default="cmake")
    args = cli.parse_args()
    if args.jobs < 1:
        cli.error("--jobs must be positive")
    args.bootstrap = args.bootstrap.resolve(strict=True)
    args.native_tools = args.native_tools.resolve(strict=True)
    args.sysroot = args.sysroot.resolve(strict=True)
    work = args.work.resolve() / args.host
    temp = work / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(temp), SOURCE_DATE_EPOCH="1793664000", ZERO_AR_DATE="1", LC_ALL="C", TZ="UTC")
    build = work / "build"
    host_tools(args, build, cross=cross_options(args))
    publish(args.host, build, args.output.resolve() / args.host / "wrcc")


if __name__ == "__main__":
    main()
