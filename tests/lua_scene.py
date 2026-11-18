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
REPORTS = ("permission.report", "module.permission.report")
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

local function query(report, prefix, family, func, capacity)
  return report(nil, prefix .. string.pack("<s8s8I8", family, func, 0), capacity)
end
for _, target in ipairs({
  {wros["permission.report"], ""},
  {wros["module.permission.report"], string.pack("<s8", "peer")}
}) do
  local report, prefix = target[1], target[2]
  for _, family in ipairs({"rosv2", "preloaddl", "ros1v1", "ros2v1"}) do
    local size_status, empty, need = query(report, prefix, family, "", 1)
    assert(size_status == 90 and empty == nil and need >= 40)
    local code, page, written = query(report, prefix, family, "", need)
    assert((code == 0 or code == 95) and #page == need and written == need)
    assert(string.unpack("<I8", page) == (code == 0 and 1 or 0))
    if family == REQUIRE_UNCOMPILED then assert(code == 95) end
  end
  local unsupported, absent, length = query(report, prefix, "rosv2", "no.such.function", 1024)
  assert(unsupported == 95 and absent == nil and length == 0)
end
local forbidden, private, length = query(wros["module.permission.report"], string.pack("<s8", "ungranted"), "rosv2", "", 1024)
assert(forbidden == 13 and private == nil and length == 0)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--address-bits", required=True, type=int, choices=(32, 64))
    parser.add_argument("--frontend-root", type=Path, default=ROOT)
    parser.add_argument("--require-uncompiled", choices=("preloaddl", "ros1v1", "ros2v1"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--no-mte", action="store_true")
    mode.add_argument("--candidate-mte", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    group = cgroup_record()
    if int(group["memory_max"]) != 68719476736 or int(group["swap_max"]) != 0:
        raise RuntimeError("expected 64 GiB qualification cgroup")
    out.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(out)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    front = args.frontend_root.resolve()
    schema = front / "share/abi/ros.json"
    all_operations = [entry["name"] for entry in json.loads(schema.read_bytes())["operations"]]
    workflow = front / "examples/lua/guard.lua"
    inputs = [workflow, schema, front / "language/lua/scene.hpp", front / "language/lua/entry.cpp",
              front / "bin/wrlua", Path(__file__), args.runtime, args.sysroots]
    report = {"complete": False, "cgroup": group, "operations": len(all_operations),
              "inputs": {str(path): sha(path) for path in inputs}, "cases": []}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2))

    def run(name, command, diagnostic=None):
        result = subprocess.run(command, cwd=out, capture_output=True, timeout=180)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        passed = result.returncode == 0 if diagnostic is None else result.returncode != 0 and diagnostic in result.stderr
        report["cases"].append(dict(name=name, exit=result.returncode, passed=passed, expected_success=diagnostic is None))
        save()
        if not passed:
            raise RuntimeError(name + ": " + result.stderr.decode(errors="replace")[-1600:])

    compiler = [sys.executable, front / "bin/wrlua", "--toolchain", args.toolchain.resolve(),
                "--sysroots", args.sysroots.resolve(), "--target", f"wasm{args.address_bits}",
                "--guest-seed", "5", "--no-mte" if args.no_mte else "--legacy-mte" if args.candidate_mte else "--mte"]
    sample = out / "application.lua"
    sample.write_text(workflow.read_text() + CHECKS.replace("REQUIRE_UNCOMPILED",
                      json.dumps(args.require_uncompiled) if args.require_uncompiled else "nil"))
    guest = out / "application.wasm"
    for label, operations in (("catalog", all_operations), ("selected", GUARD + REPORTS)):
        run(label, [*compiler, *[arg for name in operations for arg in ("--ros-operation", name)], sample, "-o", guest])
        names = {(row["module"], row["name"]) for row in inspect(guest.read_bytes())}
        if names != {("uwvm_ros_v2", name) for name in operations}:
            raise RuntimeError("incorrect linked imports")
    artifact = sha(guest)
    run("unknown-operation", [*compiler, "--ros-operation", "missing.operation", sample, "-o", guest],
        b"unknown ROSv2 operation")
    assert sha(guest) == artifact
    scene = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
    for op in GUARD + REPORTS:
        scene += ["--ros-scene-interface", "robot", op, "allow"]
    grants = ["--ros-scene-grant", "robot", "signal", "guard", "signal", "local", "guard.create,guard.trigger,guard.take",
              "--ros-scene-grant", "robot", "limited", "guard", "limited", "local", "guard.create"]
    peer = out / "report-peer.wasm"
    peer.write_bytes(b"\0asm\1\0\0\0")
    grants += ["--ros-scene-create", "peers", "--ros-scene-bind", "peers", "report-peer",
               "--wasm-preload-library", str(peer), "report-peer", "--ros-scene-grant", "robot",
               "peer", "module", "report-peer", "metadata", "module.permission.report"]
    for engine in ("int", "aot"):
        base = [args.runtime.resolve(), *Profile(args.address_bits).uwvm_feature_flags(), "--runtime-" + engine,
                "--wasm-set-main-module-name", "main", "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit"]
        if args.no_mte:
            base.append("--wasm-feature-disable-memtag-extension")
        run(engine + "-hidden", [*base, "--run", guest], b"ROS scene interface is hidden")
        run(engine + "-without-grant", [*base, *scene, "--run", guest], b"unreachable")
        run(engine + "-guard", [*base, *scene, *grants, "--run", guest])
    assert all(sha(Path(path)) == digest for path, digest in report["inputs"].items())
    report.update(complete=True, guest_sha256=artifact)
    save()


if __name__ == "__main__":
    main()
