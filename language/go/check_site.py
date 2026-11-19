"""@brief Verify an operator-signed release of the standard-Go scalar producer."""
import hashlib
import json
from pathlib import Path
import re
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
import local_release
from artifacts import unique_object


def compiler_inputs(sdk):
    """@brief Measure the SDK files controlling emitted Go guest code."""
    paths = ("bin/wrgo", "language/go/driver.py", "language/go/registers.py",
             "language/go/check_site.py", "language/go/release.json", "language/go/linux-amd64/producer.xz")
    result = {}
    for name in paths:
        result[name] = hashlib.sha256(local_release.read_file(sdk / name, 32 << 20)).hexdigest()
    return result


def verify(data, sdk=SDK):
    """@brief Verify one exact local WSEA release before using a site compiler.
    @param data Operator-provided JSON with trust configuration and a release digest.
    @param sdk Installed development selection whose compiler and encoder are measured.
    @return SHA-256 of the verified row binding the compiler, engine and test evidence.
    @details No sysroot or replacement compiler is loaded from operator data. The
    module must describe the bounded, memory-free Go profile and both VM engines.
    """
    site = json.loads(data, object_pairs_hook=unique_object)
    if not isinstance(site, dict) or set(site) != {"trust", "release_sha256"}:
        raise ValueError("a Go site requires trust and an exact signed release digest")
    rows = local_release.verified_releases(site["trust"])
    inputs = compiler_inputs(sdk)
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"format", "language", "inputs", "vm_sha256", "tests"}:
            continue
        if (row["format"] != "wros-go-register-site" or row["language"] != "go"
                or row["inputs"] != inputs or not isinstance(row["tests"], dict)
                or set(row["tests"]) != {"int", "aot", "admission", "xmake"}):
            continue
        values = [row["vm_sha256"], *row["tests"].values()]
        if not all(isinstance(value, str) and re.fullmatch("[a-f0-9]{64}", value) for value in values):
            continue
        digest = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if digest == site["release_sha256"]:
            return digest
    raise ValueError("no matching verified standard-Go site release")


if __name__ == "__main__":
    print(verify(sys.stdin.buffer.read(32769)))
