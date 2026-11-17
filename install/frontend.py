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

ROOT = Path(__file__).resolve().parents[1]

def audit(data, threads):
    abi = json.loads((ROOT / "share/abi/ros.json").read_text())
    approved = {(abi["module"], r["name"]): (r["wasm_signature"]["parameters"], r["wasm_signature"]["results"])
                for r in abi["operations"]}
    for name in ("environ_get", "environ_sizes_get"):
        approved["wasi_snapshot_preview1", name] = (["i32", "i32"], ["i32"])
    approved["wasi_snapshot_preview1", "proc_exit"] = (["i32"], [])
    if threads:
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
    a = parser.parse_args()
    try:
        profile = Profile(int(a.target[4:]), "1.0" if a.core=="mvp" else "3.0", a.threads, a.mte,
                          "eh" if (a.eh if a.eh is not None else a.core!="mvp") else "noeh")
        if any(not re.fullmatch(r"[a-zA-Z_]\w*", n,re.ASCII) for n in a.export):
            raise ValueError("invalid Wasm export name")
        sources=[p.resolve(strict=True) for p in a.sources]
        if a.output.resolve() in sources:
            raise ValueError("output aliases an input")
        if any(p.suffix not in (".c",".cc",".cxx",".cpp",".C") for p in sources):
            raise ValueError("this frontend takes C or C++ source files")
        with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
            staged=Path(td)/"module.wasm"
            args=["-O"+a.O, "-I"+str(ROOT/"include"), *(["-g"] if a.g else [])]
            if a.reactor: args += ["-nostartfiles","-Wl,--no-entry"]
            args += ["-Wl,--export="+n for n in a.export]
            args += [*map(str,sources), "-o",str(staged)]
            command, _ = make_command(a.toolchain,a.sysroots,profile,language,args,verify=True)
            subprocess.run(command,check=True)
            audit(staged.read_bytes(),a.threads)
            os.replace(staged,a.output)
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as exc:
        parser.exit(1,f"{parser.prog}: {exc}\n")
    return 0
