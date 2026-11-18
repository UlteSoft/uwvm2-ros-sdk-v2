"""Wasm-only C and C++ compiler driver. Validate imports before publishing output."""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from compiler import make_command
from guest_profile import Profile
from imports import inspect
import artifacts

ROOT = Path(__file__).resolve().parents[1]

def audit(data, profile):
    """Allow exact ROS signatures and the selected pointer-width Preview1 ABI.

    Preview1 does not standardize memory64: the matching UWVM sysroot uses
    explicit *_wasm64 imports. Neither spelling grants runtime permission.
    """
    abi = json.loads((ROOT / "share/abi/ros.json").read_text())
    approved = {(abi["module"], r["name"]): (r["wasm_signature"]["parameters"], r["wasm_signature"]["results"])
                for r in abi["operations"]}
    suffix = "_wasm64" if profile.address_bits == 64 else ""
    pointer = "i" + str(profile.address_bits)
    for name in ("environ_get", "environ_sizes_get"):
        approved["wasi_snapshot_preview1", name + suffix] = ([pointer, pointer], ["i32"])
    approved["wasi_snapshot_preview1", "clock_res_get" + suffix] = (["i32", pointer], ["i32"])
    approved["wasi_snapshot_preview1", "clock_time_get" + suffix] = (["i32", "i64", pointer], ["i32"])
    approved["wasi_snapshot_preview1", "proc_exit" + suffix] = (["i32"], [])
    if profile.threads and profile.address_bits != 32:
        raise ValueError("no qualified memory64 thread startup ABI is available")
    if profile.threads:
        approved["wasi", "thread-spawn"] = (["i32"], ["i32"])
    for row in inspect(data):
        expected = approved.get((row["module"], row["name"]))
        if row["kind"] != 0 or expected != (row.get("params"), row.get("results")):
            raise ValueError(f"unauthorized import or signature {row['module']}.{row['name']}")

def main(language):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("--sysroots", required=True, action="append", type=Path)
    parser.add_argument("--target", choices=("wasm32","wasm64"), default="wasm32")
    parser.add_argument("--core", choices=("mvp","3.0"), default="3.0")
    parser.add_argument("--eh", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("-pthread","--threads", action="store_true")
    parser.add_argument("--reactor", action="store_true")
    parser.add_argument("--export", action="append", default=[])
    parser.add_argument("-O", choices=list("0123sz"), default="2")
    parser.add_argument("-g", action="store_true")
    parser.add_argument("-c", "--compile-only", action="store_true")
    parser.add_argument("-I", "--include-dir", action="append", default=[], type=Path)
    parser.add_argument("-D", "--define", action="append", default=[])
    parser.add_argument("--std", choices=("c11", "c17", "c23") if language == "c" else
                        ("c++17", "c++20", "c++23"))
    a = parser.parse_args()
    try:
        profile = Profile(int(a.target[4:]), "1.0" if a.core=="mvp" else "3.0", a.threads, a.mte,
                          "eh" if (a.eh if a.eh is not None else a.core!="mvp") else "noeh")
        if any(not re.fullmatch(r"[a-zA-Z_]\w*", n,re.ASCII) for n in a.export):
            raise ValueError("invalid Wasm export name")
        sources=[p.resolve(strict=True) for p in a.sources]
        if a.output.resolve() in sources:
            raise ValueError("output aliases an input")
        if len(sources) > artifacts.MAX_MEMBERS:
            raise ValueError("too many compiler inputs")
        if any(p.suffix not in (".c",".cc",".cxx",".cpp",".C",".o",".a") for p in sources):
            raise ValueError("expected C/C++ sources or WROS .o/.a build artifacts")
        if a.compile_only and (len(sources) != 1 or sources[0].suffix in (".o", ".a") or a.reactor or a.export):
            raise ValueError("-c requires one source and no final-link options")
        if any(not re.fullmatch(r"[a-zA-Z_]\w*(?:=[^\r\n\x00]*)?", n, re.ASCII) for n in a.define):
            raise ValueError("invalid preprocessor definition")
        includes = [p.resolve(strict=True) for p in a.include_dir]
        if any(not p.is_dir() for p in includes):
            raise ValueError("include path is not a directory")
        with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
            staged=Path(td)/("unit.o" if a.compile_only else "module.wasm")
            args=["-O"+a.O, "-I"+str(ROOT/"include"), *(["-g"] if a.g else [])]
            args += ["-I" + str(p) for p in includes] + ["-D" + n for n in a.define]
            if a.std: args += ["-std=" + a.std]
            if a.compile_only: args += ["-c"]
            if a.reactor: args += ["-nostartfiles","-Wl,--no-entry"]
            args += ["-Wl,--export="+n for n in a.export]
            # Resolve the compiler/sysroot first; require that exact profile for
            # every separately compiled input. Copy validated object bytes into
            # our private work directory so later path replacement cannot race.
            command, record = make_command(a.toolchain,a.sysroots,profile,language,args,verify=True)
            inputs = artifacts.stage_inputs(sources, Path(td), profile.to_dict(), record["compiler_sha256"], a.toolchain)
            command += [*map(str, inputs), "-o",str(staged)]
            # Archive dependencies must precede libunwind in static link order.
            if "-lunwind" in command:
                command.remove("-lunwind")
                command.append("-lunwind")
            subprocess.run(command,check=True)
            data = artifacts.read_bounded(staged)
            if a.compile_only:
                data = artifacts.seal_object(data, profile.to_dict(), record["compiler_sha256"])
            else:
                data = artifacts.strip_notes(data)
                audit(data,profile)
            staged.write_bytes(data)
            os.replace(staged,a.output)
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        parser.exit(1,f"{parser.prog}: {exc}\n")
    return 0
