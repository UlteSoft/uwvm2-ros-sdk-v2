"""Exercise an operator-selected WebAssembly-only Flang and reject native code generation."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys

from separate_compilation import ROOT, cgroup_record, sha
sys.path.insert(0, str(ROOT / "language/fortran"))
from flang_identity import MULTI_TARGET_DEVELOPMENT_FLANG, require_compiler
from artifacts import sections


def uses_memory64(data):
    """Read the target_features vector from the relocatable Wasm object."""
    feature_sections = [body for _, _, name, body in sections(data) if name == "target_features"]
    if len(feature_sections) != 1:
        raise ValueError("expected one LLVM target_features section")
    features = feature_sections[0]
    width = None
    for _ in range(features.count()):
        prefix, name = features.byte(), features.name()
        if name == "memory64":
            if width is not None or prefix not in (ord("+"), ord("-")):
                raise ValueError("invalid memory64 target feature")
            width = prefix == ord("+")
    features.end()
    return width is True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flang", required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--approved-sha256", required=True)
    parser.add_argument("--output", required=True, type=lambda p: Path(p).resolve())
    args = parser.parse_args()
    record = dict(complete=False, cgroup=cgroup_record(), cases=[], compiler=sha(args.flang))
    if record["compiler"] != args.approved_sha256 or record["compiler"] == MULTI_TARGET_DEVELOPMENT_FLANG:
        raise ValueError("qualification requires an approved WebAssembly-only Flang")
    require_compiler(args.flang)
    args.output.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    source = args.output / "probe.f90"
    source.write_text("integer(4) function measure(i) bind(c)\ninteger(4), value :: i\nmeasure=i+1\nend function\n")
    receipt = args.output / "results.json"
    for triple in ("wasm32-unknown-wasip1", "wasm64-unknown-wasip1", "x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu"):
        wasm = triple.startswith("wasm")
        obj = args.output / (triple + ".o")
        command = [args.flang, "-fc1", "-triple", triple, "-emit-obj", "-O3",
                   "-debug-info-kind=standalone", source, "-o", obj]
        proc = subprocess.run(command, cwd=args.output, capture_output=True, timeout=60)
        (args.output / (triple + ".log")).write_bytes(proc.stderr)
        data = obj.read_bytes() if obj.is_file() else b""
        record["cases"].append(dict(name=triple, code=proc.returncode, expected_success=wasm,
                                    object_sha256=sha(obj) if data else None))
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        if (proc.returncode == 0) != wasm or (wasm and not data.startswith(b"\x00asm\x01\x00\x00\x00")) or (not wasm and data):
            raise RuntimeError("Flang produced an unexpected result for " + triple)
        if wasm and uses_memory64(data) != triple.startswith("wasm64"):
            raise RuntimeError("memory64 target feature mismatch")
    if sha(args.flang) != record["compiler"]:
        raise ValueError("Flang changed during qualification")
    record["complete"] = True
    receipt.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
