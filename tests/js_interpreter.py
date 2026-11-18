"""Build a selected JavaScript SDK application with xmake and exercise scoped ROS guards in both VM engines."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("sdk", "vm", "xmake", "output"):
        p.add_argument("--" + flag, type=Path, required=True)
    args = p.parse_args()
    out, sdk, vm = args.output.resolve(), args.sdk.resolve(strict=True), args.vm.resolve(strict=True)
    sys.path.insert(0, str(sdk / "install"))
    from guest_profile import Profile
    from imports import inspect
    out.mkdir(parents=True)
    for name in ("xmake.lua", "body.js"):
        shutil.copyfile(sdk / "examples/js" / name, out / name)
    state = dict(complete=False, vm=digest(vm), sdk=str(sdk), cgroup=Path("/proc/self/cgroup").read_text().strip(), steps=[])
    env = {**os.environ, "PATH": "/usr/bin:/bin", "TMPDIR": str(out), "XMAKE_GLOBALDIR": str(out / "global"),
           "UWVM_ROS_SDK_ROOT": str(sdk), "WROS_PLATFORM": sdk.parents[1].name, "PYTHONDONTWRITEBYTECODE": "1"}
    for key in ("WROS_TOOLCHAIN", "WROS_SYSROOTS"):
        env.pop(key, None)

    def save():
        (out / "results.json").write_text(json.dumps(state, indent=2) + "\n")

    def run(name, argv, refusal=None):
        cmd = list(map(str, argv))
        log = out / (name + ".log")
        with log.open("xb") as stream:
            result = subprocess.run(cmd, cwd=out, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=420)
        state["steps"].append(dict(name=name, argv=cmd, status=result.returncode, log=digest(log)))
        save()
        if refusal is None:
            result.check_returncode()
        elif not result.returncode or refusal not in log.read_text(errors="replace"):
            raise ValueError("unexpected failure for " + name)

    run("configure", [args.xmake, "f", "-p", "wasm-wasip1", "-a", "wasm32", "-y"])
    run("build", [args.xmake, "-v", "robot"])
    wasm, = (out / "build").rglob("robot.wasm")
    backend = Path(str(wasm) + ".wros-build.json")
    javascript = Path(str(wasm) + ".wros-js.json")
    build = json.loads(backend.read_bytes())
    js = json.loads(javascript.read_bytes())
    expected = ["capability.close", "capability.open", "guard.create", "guard.take", "guard.trigger"]
    assert js["operations"] == expected and js["backend_build_sha256"] == digest(backend)
    assert js["wasm_sha256"] == digest(wasm) and js["script_sha256"] == digest(out / "body.js")
    assert build["language"] == "c" and build["mode"] == "strict" and build["vm_sha256"] == digest(vm)
    assert {(i["module"], i["name"]) for i in inspect(wasm.read_bytes())} == {
        *(("uwvm_ros_v2", name) for name in expected), ("wasi_snapshot_preview1", "clock_time_get")}
    run("verify", [sys.executable, "-B", sdk/"install/qualification.py", "--artifact", wasm, "--vm", vm,
                   "--receipt", backend, "--approved-receipt-sha256", digest(backend)])
    clock = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main", "--wasip1-single-interface",
             "main", "clock_time_get", "allow", "--wasip1-single-grant", "main", "realtime-clock"]
    interfaces = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
    for op in expected:
        interfaces.extend(["--ros-scene-interface", "robot", op, "allow"])
    grant = ["--ros-scene-grant", "robot", "signal", "guard", "signal", "local", "guard.create,guard.trigger,guard.take"]
    for engine in ("int", "aot"):
        base = [vm, *Profile(32).uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main",
                "--debug-fault-action", "exit", *clock]
        run(engine + "-hidden", [*base, "--run", wasm], "ROS scene interface is hidden")
        run(engine + "-ungranted", [*base, *interfaces, "--run", wasm], "unreachable")
        run(engine + "-allowed", [*base, *interfaces, *grant, "--run", wasm])
    state.update(complete=True, artifact=digest(wasm), backend_receipt=digest(backend), js_receipt=digest(javascript))
    save()


if __name__ == "__main__":
    main()
