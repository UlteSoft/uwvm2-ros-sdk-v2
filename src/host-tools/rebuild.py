"""Rebuild Xmake or the SDK scene VM for a supported Linux userspace ABI."""
import argparse
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
VM_TARGETS = {"linux-x86_64": ("x86_64-linux-gnu", "X86"), "linux-i686": ("i686-linux-gnu", "X86"),
              "linux-arm": ("arm-linux-gnueabi", "ARM"), "linux-armhf": ("arm-linux-gnueabihf", "ARM"),
              "linux-aarch64": ("aarch64-linux-gnu", "AArch64")}


def build_xmake(source, work, jobs, env, host, xmake):
    # The shell build supplies a stage-1 Xmake with external scripts. Its core
    # project then uses the upstream embed rule to compile the Lua archive in.
    if not shutil.which("zig", path=env["PATH"]):
        raise ValueError("the static Xmake bundle build needs Zig on PATH")
    if xmake is None:
        bootstrap = work / "bootstrap"
        subprocess.run(["sh", "configure", "--prefix=" + str(bootstrap)], cwd=source, env=env, check=True)
        subprocess.run(["make", "-j", str(jobs)], cwd=source, env=env, check=True)
        subprocess.run(["make", "install", "PREFIX=" + str(bootstrap), "DESTDIR="], cwd=source, env=env, check=True)
        xmake = bootstrap / "bin/xmake"
    origin = json.loads((HERE / "xmake/UPSTREAM.json").read_bytes())
    target = origin[host.replace("-", "_")]
    build = work / "build"
    core = source / "core"
    subprocess.run([xmake, "f", "-c", "-y", "-p", "linux", "-a", target["xmake_arch"], "-m", "release", "-o", build,
                    "--embed=y", "--toolchain=zig", "--cross=" + target["zig_target"]],
                   cwd=core, env=env, check=True)
    subprocess.run([xmake, "build", "-j", str(jobs), "cli"], cwd=core, env=env, check=True)
    return build / "xmake"


def cross_vm_options(args, work, env):
    triple, _ = VM_TARGETS[args.host]
    sysroot = args.sysroot.resolve(strict=True)
    if args.gcc_install_dir:
        gcc = args.gcc_install_dir.resolve(strict=True)
    else:
        # Debian GNU sysroots include target startup objects and libatomic here.
        roots = sorted((sysroot / "usr/lib/gcc" / triple).glob("*/libgcc.a"))
        if len(roots) != 1:
            raise ValueError("select the target GCC library directory with --gcc-install-dir")
        gcc = roots[0].parent
    native_bin = args.llvm_native_bin.resolve(strict=True)
    for tool in ("llvm-tblgen", "llvm-min-tblgen"):
        if not os.access(native_bin / tool, os.X_OK):
            raise ValueError(f"missing build-host generator: {native_bin / tool}")
    cc = shutil.which("clang", path=env["PATH"])
    cxx = shutil.which("clang++", path=env["PATH"])
    if not cc or not cxx or not (gcc / "libgcc.a").is_file():
        raise ValueError("a cross VM build needs clang, clang++ and the target libgcc.a")
    if not (gcc / "libatomic.a").is_file():
        raise ValueError(f"missing target static atomic library: {gcc / 'libatomic.a'}")
    arch = args.host.removeprefix("linux-")
    gcc_flag = "--gcc-install-dir=" + str(gcc)
    compiler_flags = [gcc_flag]
    if arch in ("arm", "armhf"):
        compiler_flags.append("-march=armv7-a")
    if arch == "armhf":
        compiler_flags.extend(["-mfloat-abi=hard", "-mfpu=vfpv3-d16"])
    link_flags = [gcc_flag, "-fuse-ld=lld"]
    # The arm-linux-gnueabi triple selects base AAPCS. The dependency toolchain
    # also states the soft-float choice explicitly for CMake's compiler checks.
    cmake_flags = compiler_flags + (["-mfloat-abi=soft"] if arch == "arm" else [])
    values = dict(processor="armv7" if arch in ("arm", "armhf") else arch, sysroot=str(sysroot),
                  cc=cc, cxx=cxx, triple=triple, native_bin=str(native_bin), tablegen=str(native_bin / "llvm-tblgen"),
                  compile_flags=shlex.join(cmake_flags), link_flags=shlex.join(link_flags))
    template = (HERE / "uwvm2-ros/linux-cross.cmake.in").read_text()

    def cmake_value(match):
        value = values[match[1]]
        delimiter = "="
        while f"]{delimiter}]" in value:
            delimiter += "="
        return f"[{delimiter}[{value}]{delimiter}]"

    toolchain = work / "target.cmake"
    toolchain.write_text(re.sub(r"@(\w+)@", cmake_value, template))
    return ["--target=" + triple, "--llvm-target=" + triple, "--sysroot=" + str(sysroot), "--rtlib=libgcc",
            "--llvm-cmake-toolchain=" + str(toolchain), "--cxflags=" + shlex.join(compiler_flags),
            "--ldflags=" + shlex.join(link_flags)]


def build_vm(source, work, args, env, xmake, cross):
    build = work / "build"
    arch = args.host.removeprefix("linux-")
    triple, backend = VM_TARGETS[args.host]
    march = "armv7-a" if arch in ("arm", "armhf") else "none"
    options = cross_vm_options(args, work, env) if cross else []
    if not cross and arch != "x86_64":
        # Xmake reports CPU aliases such as arm64 and i386. Keep an explicit
        # GNU userspace triple, including the ARM float calling convention.
        toolchain = work / "native.cmake"
        toolchain.write_text("".join(f"set(CMAKE_{language}_COMPILER_TARGET {triple})\n" for language in ("C", "CXX", "ASM")) +
                             f'set(LLVM_HOST_TRIPLE {triple} CACHE STRING "VM host triple" FORCE)\n' +
                             f'set(LLVM_DEFAULT_TARGET_TRIPLE {triple} CACHE STRING "VM code generation triple" FORCE)\n')
        options = ["--target=" + triple, "--llvm-target=" + triple, "--llvm-cmake-toolchain=" + str(toolchain)]
        if arch == "armhf":
            options.append("--cxflags=-mfloat-abi=hard -mfpu=vfpv3-d16")
    subprocess.run([xmake, "f", "-y", "-p", "linux", "-a", arch, "-m", "release", "-o", build,
                    "--march=" + march, "--use-llvm-compiler=y", "--use-cxx-module=n",
                    "--execution-int=uwvm-int", "--execution-jit=llvm", "--import-u2rosv2=y",
                    "--enable-local-imported-wasip1-socket=none", "--llvm-build-targets=" + backend,
                    "--llvm-runtimes-provider=bundled", "--openssl-provider=bundled", *options,
                    "--llvm-build-jobs=" + str(args.jobs), "--openssl-build-jobs=" + str(args.jobs)],
                   cwd=source, env=env, check=True)
    subprocess.run([xmake, "build", "-j", str(args.jobs), "uwvm2-ros"], cwd=source, env=env, check=True)
    return build / "linux" / arch / "release/uwvm2-ros"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("tool", choices=("xmake", "uwvm2-ros"))
    cli.add_argument("--host", choices=VM_TARGETS, help="output userspace ABI (default: this Linux process)")
    cli.add_argument("--output", required=True, type=Path, help="new executable path")
    cli.add_argument("--jobs", type=int, default=1)
    cli.add_argument("--work", type=Path, default=Path.cwd() / ".tmp", help="parent of the temporary build tree")
    cli.add_argument("--xmake", type=Path, help="build-host Xmake (VM default: installed SDK bin/xmake)")
    cli.add_argument("--clang-bin", type=Path, help="C++26 Clang bin directory for a VM build")
    cli.add_argument("--sysroot", type=Path, help="target GNU/Linux development sysroot for a cross VM build")
    cli.add_argument("--gcc-install-dir", type=Path, help="target GCC directory containing libgcc.a")
    cli.add_argument("--llvm-native-bin", type=Path, help="build-host table generators from the bundled LLVM revision")
    args = cli.parse_args()
    installer = runpy.run_path(str(SDK / "install/install.py"))
    native_host = installer["current_host"]()
    if native_host not in VM_TARGETS:
        cli.error("a supported Linux build host is required")
    args.host = args.host or native_host
    cross = args.tool == "uwvm2-ros" and (args.host != native_host or args.sysroot is not None)
    if cross and not (args.sysroot and args.llvm_native_bin):
        cli.error("a cross VM build requires --sysroot and --llvm-native-bin")
    if not cross and (args.sysroot or args.gcc_install_dir or args.llvm_native_bin):
        cli.error("sysroot, GCC library directory and native table generators apply to cross VM builds")
    if args.jobs < 1:
        cli.error("--jobs must be positive")
    if args.tool != "uwvm2-ros" and args.clang_bin:
        cli.error("--clang-bin applies to the VM build")
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        cli.error("--output must name a new file")
    xmake = args.xmake.absolute() if args.xmake else (SDK / "bin/xmake" if args.tool == "uwvm2-ros" else None)
    if xmake and not (xmake.is_file() and os.access(xmake, os.X_OK)):
        cli.error("select an executable --xmake or install the SDK host tools first")
    work_parent = args.work.resolve()
    source_root = HERE / args.tool / "upstream"
    if work_parent.is_relative_to(source_root):
        cli.error("--work must be outside the upstream source tree")
    work_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work_parent, prefix=args.tool + "-build-") as directory:
        work = Path(directory)
        scratch = work / "tmp"
        scratch.mkdir()
        env = dict(os.environ, TMPDIR=str(scratch), TEMP=str(scratch), TMP=str(scratch),
                   XMAKE_TMPDIR=str(scratch), XMAKE_GLOBALDIR=str(work / "global"), XMAKE_CONFIGDIR=str(work / "config"),
                   XDG_CACHE_HOME=str(work / "cache"), ZIG_GLOBAL_CACHE_DIR=str(work / "zig-cache"),
                   CCACHE_DISABLE="1", PYTHONDONTWRITEBYTECODE="1")
        env.pop("XMAKE_PROGRAM_DIR", None)
        env.pop("UWVM_ROS_QUALIFIED_PREBUILT_LLVM", None)
        if args.clang_bin:
            clang_bin = args.clang_bin.resolve()
            for name in ("clang", "clang++", "ld.lld"):
                if not (clang_bin / name).is_file():
                    cli.error("missing bootstrap tool: " + str(clang_bin / name))
            env["PATH"] = os.pathsep.join([str(clang_bin), env["PATH"]])
        source = work / "source"
        shutil.copytree(source_root, source)
        if args.tool == "xmake":
            product = build_xmake(source, work, args.jobs, env, args.host, xmake)
        else:
            product = build_vm(source, work, args, env, xmake, cross)
            dynamic = subprocess.check_output(["readelf", "-dW", product], text=True, env=dict(env, LC_ALL="C"))
            if "Shared library: [libatomic.so" in dynamic:
                raise ValueError("the rebuilt VM retained a shared libatomic dependency")
        installer["require_host"](product, args.host)
        output.parent.mkdir(parents=True, exist_ok=True)
        with product.open("rb") as src, tempfile.NamedTemporaryFile(dir=output.parent) as staged:
            shutil.copyfileobj(src, staged)
            staged.flush()
            os.fchmod(staged.fileno(), 0o755)
            os.link(staged.name, output)
    print(output)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"Host tool build failed: {error}")
