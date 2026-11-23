"""Compile a freestanding Zig module with the installed Zig frontend and WROS LLVM backend."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SDK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SDK / "src/compilers/cc/policy"))
from guest_profile import Profile
from imports import inspect


def build(args):
    selection = json.loads((SDK / "selection.json").read_bytes())
    platform = args.platform or selection["platform"]
    if selection["language"] != "zig" or platform != selection["platform"]:
        raise ValueError("the requested Zig platform must match the installed selection")
    source = args.source.resolve(strict=True)
    out = args.output.absolute()
    if source.suffix != ".zig" or not source.is_file() or out.suffix != ".wasm" or source == out.resolve():
        raise ValueError("supply a Zig root source and a separate .wasm output")
    core3 = args.core == "3.0"
    bits = int(args.target[4:])
    eh = core3 if args.eh is None else args.eh
    profile = Profile(bits, "3.0" if core3 else "1.0", args.threads, args.mte, "eh" if eh else "noeh")
    profile.memory64_enabled(args.memory64)
    if args.threads:
        raise ValueError("the freestanding Zig storage backend currently supports single-threaded modules")
    wasm_tools = SDK / "share/toolchains/portable/bin"
    zig_tools = SDK / "share/toolchains/zig"
    include = SDK / "include/u2rosv2"
    with tempfile.TemporaryDirectory(dir=out.parent, prefix="wrzig-") as scratch:
        work = Path(scratch)
        raw, marked, obj, result = (work / name for name in ("guest.bc", "tagged.bc", "guest.o", "guest.wasm"))
        env = dict(PATH=os.defpath, LC_ALL="C", TZ="UTC", TMPDIR=str(work),
                   ZIG_GLOBAL_CACHE_DIR=str(work / "global"), ZIG_LOCAL_CACHE_DIR=str(work / "local"))
        def run(argv):
            subprocess.run(argv, cwd=work, env=env, check=True)

        modules = {"uwrosv2": include / "universal/zig/root.zig"}
        if platform != "generic":
            modules[platform] = include / "platform" / platform / "zig/root.zig"
        zig = [SDK / "bin/wrzig", "--wros-emit-bitcode", "--zig-lib-dir", zig_tools / "lib",
               "--cache-dir", work / "local", "--global-cache-dir", work / "global",
               "-fllvm", "-fno-libllvm", "-fno-emit-bin", "-femit-llvm-bc=" + str(raw),
               "-fno-compiler-rt", "-fno-stack-protector", "-fno-error-tracing",
               "-target", args.target + "-freestanding", "-O", "Debug"]
        for name in modules:
            zig += ["--dep", name]
        run([*zig, "-Mroot=" + str(source), *[f"-M{name}={path}" for name, path in modules.items()]])
        run([zig_tools / "bin/wros-zig-mte", str(bits), "on" if args.mte else "off", raw, marked])
        features = profile.llvm_feature_flags()
        features.append("-fsanitize=memtag" if args.mte else "-fno-sanitize=memtag")
        if eh:
            features += ["-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false"]
        else:
            features.append("-fno-exceptions")
        clang = [wasm_tools / "clang", "--no-default-config", "--target=" + profile.triple,
                 *features, "-O" + args.O]
        run([*clang, "-Wno-override-module", "-c", marked, "-o", obj])
        # MVP can lower memory intrinsics to ordinary calls. The freestanding
        # byte routines are compiled by exactly the same backend and profile.
        memory = work / "memory.o"
        run([*clang, "-ffreestanding", "-fno-builtin", "-ffunction-sections",
             "-c", Path(__file__).with_name("memory.c"), "-o", memory])
        run([wasm_tools / "wasm-ld", "-m" + args.target, "--no-entry", "--export=_start",
             "--max-memory=16777216", *([] if args.g else ["--strip-debug"]),
             obj, memory, "-o", result])
        contract = json.loads((SDK / "share/abi/ros.json").read_bytes())
        expected = {row["name"]: row["wasm_signature"] for row in contract["operations"]}
        widths = []
        for row in inspect(result.read_bytes(), memory_types=widths):
            if (row["module"] != contract["module"] or row["kind"] != 0 or
                    expected.get(row["name"]) != {"parameters": row["params"], "results": row["results"]}):
                raise ValueError(f"unregistered Zig import or signature: {row['module']}.{row['name']}")
        if widths != [bits]:
            raise ValueError("linked memory width differs from the selected Zig target")
        os.replace(result, out)


def main():
    p = argparse.ArgumentParser(prog="wrzig", description=__doc__)
    p.add_argument("--version", action="version", version="wrzig 0.16.0 (WROS LLVM WasmMTE)")
    p.add_argument("--platform", choices=("generic", "universal_robots"))
    p.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    p.add_argument("--core", choices=("3.0", "mvp"), default="3.0")
    p.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--eh", action=argparse.BooleanOptionalAction)
    p.add_argument("--memory64", action=argparse.BooleanOptionalAction)
    p.add_argument("--threads", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("-O", choices=list("0123sz"), default="3")
    p.add_argument("-g", action="store_true")
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("source", type=Path)
    try:
        build(p.parse_args())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        p.exit(1, f"wrzig: {exc}\n")


if __name__ == "__main__":
    main()
