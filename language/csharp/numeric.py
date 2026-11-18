"""Compile a freestanding C# integer method to a core wasm32 module exporting evaluate(i32) -> i32."""
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

from host import environment, REF_PACK, SDK_VERSION, sha, stage

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(SDK / "install"))
from artifacts import read_bounded, seal_object
from compiler import make_command
from private_exports import keep_private_memory
from frontend import audit
from guest_profile import Profile
from imports import inspect


def compile_guest(args, work):
    tool = args.toolchain.resolve(strict=True) / "bin"
    stage(work, args.dotnet.resolve(strict=True), args.mono_compiler.resolve(strict=True))
    host = work / "inputs/dotnet"
    compiler = work / "inputs/compiler"
    roslyn = host / "sdk" / SDK_VERSION / "Roslyn/bincore"
    refs = host / "packs/Microsoft.NETCore.App.Ref" / REF_PACK / "ref/net9.0"
    host_refs = host / "shared/Microsoft.NETCore.App" / REF_PACK
    env = environment(work, tool)

    def run(label, command, extra=None):
        result = subprocess.run(command, cwd=work, env=env | (extra or {}), timeout=150,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            raise ValueError(label + ": " + result.stdout.decode(errors="replace")[-2400:])
        return result.stdout.decode(errors="replace")

    def csc(assembly, sources, references, kind):
        debug = ["-debug:portable", "-pdb:WrosKernel.pdb", "-checksumalgorithm:SHA256"] if kind == "library" else []
        return run("Roslyn " + assembly, [host / "dotnet", roslyn / "csc.dll", "-nologo", "-noconfig",
                   "-deterministic+", *debug, "-target:" + kind, "-unsafe+", "-optimize+", "-nostdlib+",
                   *["-reference:" + str(p) for p in references], "-out:" + assembly, *sources])

    dll = "WrosKernel.dll"
    csc(dll, args.sources, [refs / filename for filename in ("mscorlib.dll", "System.Runtime.dll", "netstandard.dll")], "library")
    csc("Admit.dll", [HERE / "Admit.cs"], sorted(host_refs.glob("*.dll")), "exe")
    record = run("C# metadata", [host / "dotnet", "exec", "--runtimeconfig", roslyn / "csc.runtimeconfig.json",
                                 "Admit.dll", dll, *args.entry.split("."), "WrosKernel.pdb"]).strip().split(" ")
    row, digest, line, points = record
    if not row.isascii() or not row.isdecimal() or len(row) > 7:
        raise ValueError("invalid Mono method row")
    # Trust a sequence point only when its Portable PDB document digest matches
    # a source compiled in this invocation. The file name exposes no host path.
    files = {sha(path): path.name for path in args.sources}
    debug_args = [args.entry, files.get(digest, ""), line, points]
    run("Mono LLVMOnly", [compiler / "bin/mono-aot-cross", "--debug",
                          "--aot=llvmonly,asmonly,static,llvm-outfile=kernel.bc", dll],
        {"LD_LIBRARY_PATH": str(compiler / "lib")})
    flags = shlex.split(run("LLVM development libraries", [tool / "llvm-config", "--cxxflags", "--ldflags", "--libs",
                            "transformutils", "irreader", "bitwriter", "core", "support", "--system-libs"]))
    run("LLVM method extractor", [args.host_cxx.resolve(strict=True), "-O3", "-g", HERE / "leaf.cpp", *flags, "-o", "extract"])
    profile = Profile(mte=not args.no_mte)
    run("managed method", [work / "extract", "--mte" if profile.mte else "--no-mte", row, "kernel.bc", "leaf.bc", *debug_args])
    codegen = ["-O3", "-g", "-ffreestanding", "-c", "leaf.bc", "-o", "leaf.o"]
    closure = None
    if args.compile_only:
        command, closure = make_command(args.toolchain, [args.sysroots], profile, "c", codegen, verify=True)
    else:
        command = [tool / "clang", "--no-default-config", "--target=" + profile.triple, *profile.llvm_feature_flags(),
                   "-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false",
                   *(["-fsanitize=memtag"] if profile.mte else []), *codegen]
    run("core wasm32", command)
    run("Wasm link", [tool / "wasm-ld", "--fatal-warnings", "--no-entry", "--export=evaluate",
                      "--stack-first", "-z", "stack-size=65536", "--initial-memory=65536",
                      "--max-memory=65536", "leaf.o", "-o", "kernel.wasm"])
    guest = keep_private_memory(read_bounded(work / "kernel.wasm"), {"evaluate"}, max_pages=1)
    audit(guest, profile)
    if inspect(guest):
        raise ValueError("numeric component must have zero imports")
    if closure is not None:
        # The standalone link above has already checked that this exact leaf
        # needs no host imports. The enclosing body must pass the final SDK audit.
        guest = seal_object(read_bounded(work / "leaf.o"), profile.to_dict(), closure["compiler_sha256"], closure["closure_sha256"])
    with tempfile.NamedTemporaryFile(dir=args.output.parent, suffix=args.output.suffix, delete=False) as out:
        pending = Path(out.name)
        try:
            out.write(guest)
            out.flush()
            os.fsync(out.fileno())
            os.replace(pending, args.output)
        finally:
            pending.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for option in ("dotnet", "mono-compiler", "toolchain"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--entry", required=True, help="global static class and public method, e.g. Filter.Scale")
    parser.add_argument("--host-cxx", type=Path, default=Path("/usr/bin/g++"))
    parser.add_argument("--target", choices=("wasm32",), default="wasm32")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mte", action="store_true")
    mode.add_argument("--legacy-mte", action="store_true")
    mode.add_argument("--no-mte", action="store_true")
    parser.add_argument("-c", "--compile-only", action="store_true", help="emit a relocatable core-Wasm SDK object")
    parser.add_argument("--sysroots", type=Path, help="exact matching sysroot receipt, required for an SDK object")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("sources", nargs="+", type=Path)
    args = parser.parse_args()
    if not args.legacy_mte and not args.no_mte:
        parser.error("no signed strict C# release is available; select --legacy-mte or --no-mte explicitly")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]{0,127}\.[A-Za-z_][A-Za-z_0-9]{0,127}", args.entry):
        parser.error("expected a global Class.Method entry")
    if args.compile_only != (args.sysroots is not None):
        parser.error("use -c and --sysroots together for a relocatable SDK object")
    suffix = ".o" if args.compile_only else ".wasm"
    if args.output.suffix != suffix or not args.output.parent.is_dir():
        parser.error("expected a " + suffix + " output in an existing directory")
    try:
        args.sources = [src.resolve(strict=True) for src in args.sources]
        if (len(args.sources) > 128 or len(set(args.sources)) != len(args.sources) or
                any(not src.is_file() or src.suffix != ".cs" for src in args.sources) or
                sum(src.stat().st_size for src in args.sources) > 16 * 1024 * 1024):
            raise ValueError("expected up to 128 distinct C# files, at most 16 MiB total")
        if args.legacy_mte:
            print("warning: using unsigned C# numeric AOT with WasmMTE enabled", file=sys.stderr)
        with tempfile.TemporaryDirectory(prefix=".wrcs-", dir=args.output.parent.resolve()) as path:
            compile_guest(args, Path(path))
    except (KeyError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, "wrcs: " + str(error) + "\n")
    return 0
