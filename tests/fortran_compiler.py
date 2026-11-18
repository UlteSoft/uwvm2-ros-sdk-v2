"""Exercise an operator-selected WebAssembly-only Flang and reject native code generation."""
import argparse
import json
from pathlib import Path
import re
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
    source.write_text("integer(4) function measure(i) bind(c)\ninteger(4), value :: i\nmeasure=i+1\nend function\n"
                      "subroutine measure_tail(n, a)\ninteger :: n\nreal :: a(*)\nif (n>0) a(n)=a(1)+1.0\nend subroutine\n")
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
    for width in (32, 64):
        # An assumed-size extent is a signed -1 in the target index type, including debug uses.
        ir = args.output / f"assumed-extent-{width}.ll"
        command = [args.flang, "-fc1", "-triple", f"wasm{width}-unknown-wasip1", "-emit-llvm", "-O0",
                   "-debug-info-kind=standalone", source, "-o", ir]
        proc = subprocess.run(command, cwd=args.output, capture_output=True, timeout=60)
        (args.output / f"assumed-extent-{width}.log").write_bytes(proc.stderr)
        record["cases"].append(dict(name=f"assumed-size-debug-{width}", code=proc.returncode))
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        proc.check_returncode()
        text = ir.read_text()
        if (f"@llvm.fake.use(i{width} -1)" not in text or "!DISubrange(" not in text or
                "emissionKind: FullDebug" not in text):
            raise RuntimeError("incorrect debug index for assumed-size Fortran array")
    kind_source = args.output / "address_kind.f90"
    kind_source.write_text(
        "integer(4) function address_kinds(x) bind(c)\n"
        "  integer(4), target :: x\n"
        "  address_kinds=100*kind(sizeof(x)) + 10*kind(loc(x)) + kind(malloc(1))\n"
        "end function\n"
    )
    for width in (32, 64):
        # The C address kinds are independent of Fortran's default INTEGER.
        for default_kind in (4, 8):
            name = f"address-kinds-{width}-default-{default_kind}"
            ir = args.output / (name + ".ll")
            command = [args.flang, "-fc1", "-triple", f"wasm{width}-unknown-wasip1",
                       f"-fdefault-integer-{default_kind}", "-emit-llvm", "-O3", kind_source, "-o", ir]
            proc = subprocess.run(command, cwd=args.output, capture_output=True, timeout=60)
            (args.output / (name + ".log")).write_bytes(proc.stderr)
            record["cases"].append(dict(name=name, code=proc.returncode))
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            proc.check_returncode()
            expected = 111 * (width // 8)
            if not re.search(rf"\bret i32 {expected}\b", ir.read_text()):
                raise RuntimeError("LOC, MALLOC or SIZEOF disagrees with the target pointer width")
    desc_source = args.output / "array.f90"
    desc_source.write_text("subroutine store_first(a)\ninteger :: a(:)\na(1)=123\nend subroutine\n")
    for width in (32, 64):
        name = f"cfi-descriptor-{width}"
        ir = args.output / (name + ".ll")
        command = [args.flang, "-fc1", "-triple", f"wasm{width}-unknown-wasip1", "-emit-llvm",
                   "-debug-info-kind=standalone", "-O0", desc_source, "-o", ir]
        proc = subprocess.run(command, cwd=args.output, capture_output=True, timeout=60)
        (args.output / (name + ".log")).write_bytes(proc.stderr)
        record["cases"].append(dict(name=name, code=proc.returncode))
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        proc.check_returncode()
        layout = f"ptr, i{width}, i32, i8, i8, i8, i8, [1 x [3 x i{width}]]"
        if layout not in ir.read_text():
            raise RuntimeError("element size or CFI array dimensions disagree with the target pointer width")
    if sha(args.flang) != record["compiler"]:
        raise ValueError("Flang changed during qualification")
    record["complete"] = True
    receipt.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
