#!/usr/bin/env python3
"""Exercise Objective-C driver-session dispatch against a deployment-owned test peer."""
from contextlib import ExitStack
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import time

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from imports import inspect


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def exercise(options, out, peer_script, guest, platform, engine, mode, clock):
    child_socket, peer_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    from attachment_peer import issue

    processes = []
    keys = ExitStack()
    try:
        for endpoint in (child_socket, peer_socket):
            endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        vm_key, peer_key = issue(keys)
        fixture = options.vm_source.resolve() / "test/0084.ros-runtime"
        peer = subprocess.Popen([sys.executable, "-B", peer_script, fixture, options.peer_library.resolve(),
                                 str(peer_socket.fileno()), str(peer_key), mode],
                                pass_fds=(peer_socket.fileno(), peer_key), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(peer)
        peer_socket.close()
        clock_fd = os.open(f"/proc/{peer.pid}/ns/time", os.O_RDONLY | os.O_CLOEXEC)
        keys.callback(os.close, clock_fd)
        args = [str(options.runtime.resolve()), *Profile(32).uwvm_feature_flags(),
                "--debug-fault-action", "exit", "--wasm-set-main-module-name", "main", "--runtime-"+engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable"]
        if clock:
            args += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                     "--wasip1-single-interface", "main", clock, "allow", "--wasip1-single-grant", "main", "realtime-clock"]
        args += ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
        for operation in ("capability.open", "driver.connect", "driver.disconnect"):
            args += ["--ros-scene-interface", "robot", operation, "allow"]
        module = "uwvm_ros_v2.platform_extension." + platform + ".v1"
        actions = "driver.disconnect" if mode == "parent-denied" else "driver.connect,driver.disconnect"
        ids = [(bytes([n]) + bytes(15)).hex() for n in range(1, 6)]
        args += ["--ros-scene-grant", "robot", "arm", "driver", "joint", "registered-driver", actions,
                 "--ros-scene-driver-budget", "robot", "1", "1048576", "--ros-scene-driver-channel", "robot", "arm", "main",
                 str(child_socket.fileno()), str(peer.pid), str(os.getuid()), str(os.getgid()),
                 *ids, bytes(range(1, 33)).hex(), "128", "128", "1000000000", str(time.monotonic_ns()+10000000000), str(vm_key), str(clock_fd),
                 "--ros-scene-driver-schema", "robot", "arm", "device.submit", "64", "64", "8",
                 "--ros-scene", "robot", "platform_extension", module, "disable" if mode == "disabled" else "enable",
                 "--ros-scene", "robot", "platform_extension.bind", module, "arm", "--run", str(guest)]
        vm = subprocess.Popen(args, pass_fds=(child_socket.fileno(), vm_key, clock_fd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(vm)
        child_socket.close()
        peer.stdin.write((str(vm.pid)+"\n").encode())
        peer.stdin.close()
        peer.stdin = None
        _, vm_log = vm.communicate(timeout=25)
        result, peer_log = peer.communicate(timeout=5)
        case = "-".join((platform, engine, mode))
        (out / (case + ".log")).write_bytes(vm_log + peer_log)
        if vm.returncode or peer.returncode:
            raise RuntimeError(case + ": " + (vm_log + peer_log).decode(errors="replace")[-2000:])
        evidence = json.loads(result)
        assert evidence == {"packets": 2 if mode == "enabled" else 0, "effects": 0}
        return {"case": case, "argv": args, "peer": evidence}
    finally:
        child_socket.close()
        peer_socket.close()
        keys.close()
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("runtime", "vm-source", "peer-library", "toolchain", "objc-clang", "objc-runtime", "sysroots", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--platform", action="append", help="Defaults to every common robot platform foundation")
    parser.add_argument("--mte", choices=("strict", "candidate"), default="strict")
    opts = parser.parse_args()
    group = cgroup_record()
    assert int(group["memory_max"]) == 68719476736 and int(group["swap_max"]) == 0
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    bank = ROOT / "share/targets.json"
    platforms = list(json.loads(bank.read_text())["platforms"])
    selected = opts.platform or platforms
    assert all(name in platforms for name in selected)
    root = opts.vm_source.resolve()
    sys.path.insert(0, str(root / "test/0084.ros-runtime"))
    peer_script = ROOT / "tests/objectc/tls_peer.py"
    source = ROOT / "tests/objectc/platform_session.m"
    out = opts.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    inputs = [Path(__file__), opts.runtime, peer_script, opts.peer_library.resolve(), root/"test/0084.ros-runtime/attachment_peer.py", source, bank, opts.objc_clang, opts.objc_runtime/"runtime.json", opts.sysroots]
    report = {"complete": False, "inputs": {str(p): digest(p) for p in inputs}, "cgroup": group,
              "scope": "GNUstep driver connect/release, pinned mutual TLS 1.3 over authenticated local kernel IPC, no physical actuator", "cases": []}
    guests = {}
    try:
        for denied in (False, True):
            guest = out / ("denied.wasm" if denied else "enabled.wasm")
            argv = [ROOT / "bin/wrobjc", "--toolchain", opts.toolchain.resolve(), "--objc-runtime", opts.objc_runtime.resolve(),
                    "--objc-clang", opts.objc_clang.resolve(), "--sysroots", opts.sysroots.resolve(),
                    "--legacy-mte" if opts.mte == "candidate" else "--mte", "--target", "wasm32",
                    "-O3", "-g", "--reactor", "--export", "_start", "-DEXPECT_DENIAL="+str(int(denied)), source, "-o", guest]
            subprocess.run(argv, check=True)
            observed = {(i["module"],i["name"]) for i in inspect(guest.read_bytes())}
            clock = "clock_time_get" if ("wasi_snapshot_preview1", "clock_time_get") in observed else None
            required = {("uwvm_ros_v2", "capability.open"), ("uwvm_ros_v2", "driver.connect")}
            permitted = required | {("uwvm_ros_v2", "driver.disconnect"), ("wasi_snapshot_preview1", "clock_time_get")}
            assert required <= observed <= permitted
            if not denied: assert ("uwvm_ros_v2", "driver.disconnect") in observed
            guests[denied] = (guest, clock)
        report["guests"] = {g.name: digest(g) for g, _ in guests.values()}
        for platform in selected:
            for engine in ("int", "aot"):
                for mode in ("enabled", "disabled", "parent-denied"):
                    guest, clock = guests[mode != "enabled"]
                    result = exercise(opts, out, peer_script, guest, platform, engine, mode, clock)
                    report["cases"].append(result)
            print(platform, len(report["cases"]), flush=True)
        report["complete"] = all(digest(Path(p)) == expected for p, expected in report["inputs"].items())
    finally:
        (out/"results.json").write_text(json.dumps(report, indent=2)+"\n")
    return int(not report["complete"])


if __name__ == "__main__":
    raise SystemExit(main())
