"""Lower a wrrs crate graph with the SDK's native LLVM and check the final guest imports."""
import argparse
from pathlib import Path
import subprocess
import sys

SDK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SDK / "install"))
from artifacts import read_bounded
from compiler import compiler_environment
from frontend import audit, shared_memory_link_flags
from guest_profile import Profile


def lower(args):
    profile = Profile(int(args.target[4:]), "1.0" if args.core == "mvp" else "3.0",
                      args.shared_memory_pages is not None, args.mte, "eh" if args.eh else "noeh")
    profile.memory64_enabled(args.memory64)
    tools = SDK / "share/toolchains/portable"
    clang = tools / "bin/clang"
    linker = tools / "bin/wasm-ld"
    if not clang.is_file() or not linker.is_file():
        raise ValueError("the Rust selection requires its packaged native Clang and wasm-ld")
    env = compiler_environment(tools)
    common = [clang, "--no-default-config", "--target=" + profile.triple, *profile.llvm_feature_flags(),
              "-fsanitize=memtag" if profile.mte else "-fno-sanitize=memtag"]
    if args.eh:
        common += ["-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false"]
    else:
        common += ["-fno-exceptions", "-mno-exception-handling"]
    objects = []
    for bitcode in args.crates:
        obj = bitcode.with_suffix(".o")
        subprocess.run([*common, "-O" + args.O, *(["-g"] if args.g else []),
                        "-c", bitcode, "-o", obj], env=env, check=True)
        objects.append(obj)
    link = [*common, "-fuse-ld=" + str(linker), "-nostdlib", "-Wl,--no-entry,--export=_start",
            *shared_memory_link_flags(profile, args.shared_memory_pages), *objects]
    # Rust provides core and compiler_builtins for every selected profile. Pull in
    # additional WASI/C++ ABI unwinding helpers only when their exact SDK profile exists.
    if profile.mte and args.eh and not profile.threads and profile.wasm_version == "3.0":
        lib = SDK / "lib" / profile.triple / "core3.0-eh-mte"
        link.extend(lib / name for name in ("libc++abi.a", "libunwind.a", "libc.a", "libclang_rt.builtins.a"))
    if not args.g:
        link.append("-Wl,--strip-debug")
    output = Path("guest.wasm")
    subprocess.run([*link, "-o", output], env=env, check=True)
    audit(read_bounded(output), profile, args.shared_memory_pages, memory64=args.memory64)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--target", required=True, choices=("wasm32", "wasm64"))
    cli.add_argument("--core", required=True, choices=("3.0", "mvp"))
    for flag in ("eh", "mte", "memory64"):
        cli.add_argument("--" + flag, required=True, action=argparse.BooleanOptionalAction)
    cli.add_argument("--shared-memory-pages", type=int)
    cli.add_argument("-O", choices=list("0123sz"), required=True)
    cli.add_argument("-g", action="store_true")
    cli.add_argument("crates", type=Path, nargs="+")
    try:
        lower(cli.parse_args())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"wrrs: {error}")
