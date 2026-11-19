"""@brief Exercise the installed wrpy frontend and execute the resulting guest on a real u2ros VM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """@brief Bind source compilation, import policy, guest semantics, and negative controls to an evidence file."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--engine", choices=("int", "aot"), action="append")
    a = parser.parse_args()
    sdk, vm, output = a.sdk.resolve(), a.vm.resolve(), a.output.resolve()
    output.mkdir()
    sys.path.insert(0, str(sdk / "install"))
    from guest_profile import Profile
    from imports import inspect
    def digest(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    cases = []
    def checked(label, command, failure=None):
        start = time.monotonic_ns()
        test = subprocess.run(list(map(str, command)), capture_output=True, timeout=900)
        (output / (label + ".stdout")).write_bytes(test.stdout)
        (output / (label + ".stderr")).write_bytes(test.stderr)
        cases.append(dict(name=label, exit=test.returncode, expected=failure or "success",
                          elapsed_ns=time.monotonic_ns() - start))
        if ((failure is None and test.returncode != 0) or
                (failure and (test.returncode == 0 or failure.encode() not in test.stderr))):
            raise RuntimeError(label + ": " + test.stderr[-1700:].decode(errors="replace"))
    root = Path(__file__).resolve().parents[2]
    sources = output / "app.py"
    sources.write_text("""import sys, wros, sensor
from sensor.units import squared
assert sum(squared(n) for n in range(15)) == 1015
assert sensor.count == 1 and wros.abi() == 2
assert sys.version_info[:3] == (3, 14, 8) and sys.implementation.name == 'cpython'
try:
    import _socket
except ImportError: pass
else: raise AssertionError('unexpected socket module')
try:
    open('/a-file', 'wb')
except OSError: pass
else: raise AssertionError('unexpected file creation')
""")
    init, units = output / "__init__.py", output / "units.py"
    init.write_text("from .units import squared\ncount = 1\n")
    units.write_text("def squared(n): return n*n\n")
    wrpy = [sys.executable, sdk / "bin/wrpy"]
    artifact, neighbors = output / "app.wasm", output / "neighbors.wasm"
    checked("compile", [*wrpy, sources, "--module", "sensor=" + str(init), "--module",
                         "sensor.units=" + str(units), "--ros-abi", "--build-receipt", "-o", artifact])
    checked("compile-neighbors", [*wrpy, root / "tests/cpython/neighbor.py", "--build-receipt", "-o", neighbors])
    failing = output / "failing.wasm"
    negative = output / "negative.py"
    negative.write_text("raise RuntimeError('intentional guest failure')\n")
    checked("compile-negative", [*wrpy, negative, "-o", failing])
    raw = [("wasi_snapshot_preview1", name) for name in ("clock_time_get", "clock_res_get")]
    for wasm, expected in ((artifact, [*raw, ("uwvm_ros_v2", "abi")]), (neighbors, raw)):
        assert {(r["module"], r["name"]) for r in inspect(wasm.read_bytes())} == set(expected)
        receipt = json.loads(Path(str(wasm) + ".wros-build.json").read_bytes())
        assert receipt["mode"] == "strict" and receipt["artifact_sha256"] == digest(wasm)
    before = digest(artifact)
    checked("reject-operation", [*wrpy, sources, "--ros-operation", "socket", "-o", artifact], "unknown ROSv2 operation")
    checked("reject-module", [*wrpy, sources, "--module", "wros=" + str(init), "-o", artifact], "unique import.name")
    assert before == digest(artifact)
    clocks = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main"]
    for n in ("clock_time_get", "clock_res_get"):
        clocks += ["--wasip1-single-interface", "main", n, "allow"]
    for n in ("realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution"):
        clocks += ["--wasip1-single-grant", "main", n]
    for engine in a.engine or ("int", "aot"):
        run = [vm, *Profile().uwvm_feature_flags(), "--wasm-set-main-module-name", "main", "--runtime-" + engine,
               "--runtime-compile-threads", "3", "--runtime-llvm-jit-cache-path", "disable",
               "--runtime-llvm-jit-full-policy", "legacy-light", "--runtime-memtag-mode", "sync",
               "--debug-fault-action", "exit", *clocks]
        checked("application-" + engine, [*run, "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                                           "--ros-scene-interface", "robot", "abi", "allow", "--run", artifact])
        checked("no-ros-" + engine, [*run, "--run", artifact], "ROS scene interface is hidden")
        if engine == "int":
            checked("unhandled-python-exception", [*run, "--run", failing], "unreachable")
        checked("neighbors-" + engine, [*run, "--run", neighbors])
    (output / "results.json").write_text(json.dumps(dict(vm_sha256=digest(vm),
        wasm={p.name: digest(p) for p in (artifact, neighbors, failing)}, cases=cases), indent=2) + "\n")


if __name__ == "__main__":
    main()
