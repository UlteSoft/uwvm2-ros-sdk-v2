"""Exercise the interpreted guest's Lua-to-ROS message boundary in both VM engines."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

from separate_compilation import Profile, cgroup_record, inspect, sha

ROOT = Path(__file__).resolve().parents[1]
GUARD = ("capability.open", "capability.close", "guard.create", "guard.trigger", "guard.take")
CHECKS = '''
assert(wros.close and not wros["driver.submit"])
assert(not pcall(wros.close, signal))
local denied, absent = wros.open("missing")
assert(denied == 13 and absent == nil)
assert(not pcall(create, 42, "", 8))
local granted, restricted = wros.open("limited")
assert(granted == 0)
local fail, reply = trigger(restricted, guard, 0)
assert(fail == 13 and reply == nil)
assert(not pcall(create, restricted, "", -1))
assert(not pcall(create, restricted, "", 16777217))
assert(not pcall(create, restricted, {}, 8))
local too_small, no_data = create(restricted, "", 4)
assert(too_small == 90 and no_data == nil)
assert(wros.close(restricted) == 0)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--address-bits", required=True, type=int, choices=(32, 64))
    parser.add_argument("--candidate-mte", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    group = cgroup_record()
    if int(group["memory_max"]) != 68719476736 or int(group["swap_max"]) != 0:
        raise RuntimeError("expected 64 GiB qualification cgroup")
    out.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(out)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    schema = ROOT / "share/abi/ros.json"
    all_operations = [entry["name"] for entry in json.loads(schema.read_bytes())["operations"]]
    workflow = ROOT / "examples/lua/guard.lua"
    inputs = [workflow, schema, ROOT / "language/lua/scene.hpp", ROOT / "language/lua/entry.cpp",
              ROOT / "bin/wrlua", Path(__file__), args.runtime, args.sysroots]
    report = {"complete": False, "cgroup": group, "operations": len(all_operations),
              "inputs": {str(path): sha(path) for path in inputs}, "cases": []}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2))

    def run(name, command, diagnostic=None):
        result = subprocess.run(command, cwd=out, capture_output=True, timeout=180)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        passed = result.returncode == 0 if diagnostic is None else result.returncode != 0 and diagnostic in result.stderr
        report["cases"].append(dict(name=name, exit=result.returncode, passed=passed))
        save()
        if not passed:
            raise RuntimeError(name + ": " + result.stderr.decode(errors="replace")[-1600:])

    compiler = [sys.executable, ROOT / "bin/wrlua", "--toolchain", args.toolchain.resolve(),
                "--sysroots", args.sysroots.resolve(), "--target", f"wasm{args.address_bits}",
                "--guest-seed", "5", "--legacy-mte" if args.candidate_mte else "--mte"]
    sample = out / "application.lua"
    sample.write_text(workflow.read_text() + CHECKS)
    guest = out / "application.wasm"
    for label, operations in (("catalog", all_operations), ("selected", GUARD)):
        run(label, [*compiler, *[arg for name in operations for arg in ("--ros-operation", name)], sample, "-o", guest])
        names = {(row["module"], row["name"]) for row in inspect(guest.read_bytes())}
        if names != {("uwvm_ros_v2", name) for name in operations}:
            raise RuntimeError("incorrect linked imports")
    artifact = sha(guest)
    run("unknown-operation", [*compiler, "--ros-operation", "missing.operation", sample, "-o", guest],
        b"unknown ROSv2 operation")
    assert sha(guest) == artifact
    scene = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
    for op in GUARD:
        scene += ["--ros-scene-interface", "robot", op, "allow"]
    grants = ["--ros-scene-grant", "robot", "signal", "guard", "signal", "local", "guard.create,guard.trigger,guard.take",
              "--ros-scene-grant", "robot", "limited", "guard", "limited", "local", "guard.create"]
    for engine in ("int", "aot"):
        base = [args.runtime.resolve(), *Profile(args.address_bits).uwvm_feature_flags(), "--runtime-" + engine,
                "--wasm-set-main-module-name", "main", "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit"]
        run(engine + "-hidden", [*base, "--run", guest], b"ROS scene interface is hidden")
        run(engine + "-without-grant", [*base, *scene, "--run", guest], b"unreachable")
        run(engine + "-guard", [*base, *scene, *grants, "--run", guest])
    assert all(sha(Path(path)) == digest for path, digest in report["inputs"].items())
    report.update(complete=True, guest_sha256=artifact)
    save()


if __name__ == "__main__":
    main()
