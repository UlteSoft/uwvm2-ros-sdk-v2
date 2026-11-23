#!/usr/bin/env python3
"""Build the selected real ECMAScript toolchain and measure every emitted Wasm import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk_layout import COMPILERS, CONTRACT
from imports import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", choices=("js", "typescript"), required=True)
    p.add_argument("--output", type=Path, required=True, help="new directory for source, Wasm and measured inventory")
    args = p.parse_args()
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        p.error("choose a new output directory")
    contract = json.loads(CONTRACT.read_bytes())
    rows = contract["operations"]
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        stage = Path(tmp) / "evidence"
        stage.mkdir()
        code, checks = [], []
        for row in rows:
            function = "wr_" + row["name"].replace(".", "_")
            code.append(f'import {{ {function} }} from "uwrosv2/{row["domain"]}";')
            checks.append(f'if (typeof {function} !== "function") throw Error("{function}");')
        code += checks
        code.append('if (wr_abi() !== 2) throw Error("expected ABI 2");')
        source = stage / ("app.mjs" if args.language == "js" else "app.ts")
        source.write_text("\n".join(code) + "\n")
        wasm = stage / "app.wasm"
        flags = [value for row in rows for value in ("--ros-operation", row["name"])]
        subprocess.run([sys.executable, "-B", COMPILERS / args.language / "driver.py", source,
                        *flags, "--build-receipt", "-o", wasm], check=True)
        data = wasm.read_bytes()
        signature = lambda row: (row["module"], row["name"])
        actual = sorted(inspect(data), key=signature)
        expected = [dict(module=contract["module"], name=row["name"], kind=0, params=row["wasm_signature"]["parameters"],
                         results=row["wasm_signature"]["results"]) for row in rows]
        expected.append(dict(module="wasi_snapshot_preview1", name="clock_time_get", kind=0,
                             params=["i32", "i64", "i32"], results=["i32"]))
        if actual != sorted(expected, key=signature):
            raise ValueError("Wasm type and import sections differ from the registered guest contract")
        report = dict(language=args.language, wasm_sha256=hashlib.sha256(data).hexdigest(),
                      contract_sha256=hashlib.sha256(CONTRACT.read_bytes()).hexdigest(), ros_imports=len(rows),
                      imports=actual)
        (stage / "imports.json").write_text(json.dumps(report, indent=2) + "\n")
        os.rename(stage, out)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
