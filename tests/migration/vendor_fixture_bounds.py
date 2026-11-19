"""@brief Check resource descriptor size, reserved file names and source byte integrity."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    original = out / "original"
    original.mkdir()
    source = original / "sample.bin"
    source.write_bytes(b"pinned input\n")
    project = out / "project"
    project.mkdir()
    manifest = project / "vendor-package.xml"
    shutil.copyfile(ROOT / "examples/platform/fourier/migration/c/vendor-package.xml", manifest)
    lock = project / "upstream.lock"
    correct = {"uri": "package://wros_example_fourier/sample.bin",
               "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}
    template = json.dumps([correct]).encode()
    stage = ROOT / "examples/shared/migration/c/stage_vendor.py"
    prepare = stage.with_name("prepare.py")
    cases = {}
    for label, raw, why in (("oversize", b" " * 4097, "exceeds 4096"),
                            ("reserved", json.dumps([dict(correct, uri="package://wros_example_fourier/package.xml")]).encode(), "collides"),
                            ("wrong-hash", json.dumps([dict(correct, sha256="0" * 64)]).encode(), "differs from its lock"),
                            ("invalid-entry", b"[1]", "expected one pinned"),
                            ("valid", template, "")):
        lock.write_bytes(raw)
        dest = out / label
        invocation = [sys.executable, "-I", "-B", stage, "--project", project, "--source-root", original, "--output", dest]
        result = subprocess.run(invocation, capture_output=True)
        if bool(result.returncode) != bool(why) or why not in result.stderr.decode() or dest.exists() == bool(why):
            raise ValueError(label + ": " + result.stderr.decode())
        cases[label] = result.returncode
    lock.write_bytes(b" " * 4097)
    packed = out / "packed"
    result = subprocess.run([sys.executable, "-I", "-B", prepare, "--output", packed, "--platform-lock", lock,
                            "--package-root", out / "valid"], capture_output=True)
    if not result.returncode or b"exceeds 4096" not in result.stderr or packed.exists():
        raise ValueError("oversized build lock was accepted")
    cases["prepare-oversize"] = result.returncode
    lock.write_bytes(template)
    subprocess.run([sys.executable, "-I", "-B", prepare, "--output", packed, "--platform-lock", lock,
                   "--package-root", out / "valid"], check=True)
    cases["prepare-valid"] = hashlib.sha256((packed / "selected_resource.h").read_bytes()).hexdigest()
    (out / "results.json").write_text(json.dumps({"complete": True, "cases": cases}, indent=2) + "\n")


if __name__ == "__main__":
    main()
