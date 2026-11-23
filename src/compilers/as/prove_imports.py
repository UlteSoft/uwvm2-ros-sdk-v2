#!/usr/bin/env python3
"""Link all public AS declarations and compare the actual Wasm type/import sections with the VM contract."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from driver import HERE, digest, unpack_compiler
from imports import inspect
from sdk_layout import CONTRACT, INCLUDE


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path, help="directory for the linked Wasm and measured report")
    args = p.parse_args()
    output = args.output.resolve()
    if output.exists():
        p.error("choose a new output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        work = Path(directory)
        manifest = HERE / "compiler.json"
        node = unpack_compiler(work, json.loads(manifest.read_bytes()))
        shutil.copytree(INCLUDE / "universal/as/uwrosv2", work / "uwrosv2")
        shutil.copy2(HERE / "fixtures/all_imports.ts", work)
        shutil.copy2(HERE / "fixtures/link.mjs", work)
        subprocess.run([node, "link.mjs"], cwd=work, check=True, timeout=120,
                       env={"LC_ALL": "C", "TMPDIR": str(work), "PATH": "/nonexistent"})
        artifact = work / "all_imports.wasm"
        actual = sorted(inspect(artifact.read_bytes()), key=lambda row: (row["module"], row["name"]))
        contract = json.loads(CONTRACT.read_bytes())
        expected = sorted((dict(module=contract["module"], name=op["name"], kind=0,
                                params=op["wasm_signature"]["parameters"], results=op["wasm_signature"]["results"])
                           for op in contract["operations"]), key=lambda row: (row["module"], row["name"]))
        if actual != expected:
            missing = [item for item in expected if item not in actual]
            extra = [item for item in actual if item not in expected]
            raise ValueError(f"actual imports differ: missing or mistyped {missing}; unexpected {extra}")
        result = work / "evidence"
        result.mkdir()
        report = dict(language="AssemblyScript", compiler="0.28.20", compiler_manifest_sha256=digest(manifest),
                      node_sha256=digest(Path(node)), contract_sha256=digest(CONTRACT),
                      fixture_sha256=digest(work / "all_imports.ts"), wasm_sha256=digest(artifact),
                      count=len(actual), imports=actual)
        (result / "imports.json").write_text(json.dumps(report, indent=2) + "\n")
        artifact.rename(result / artifact.name)
        os.rename(result, output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
