"""@file assemblyscript_driver_reply.py
@brief Qualify authenticated AssemblyScript result-capacity retry and erasure.
"""
from contextlib import ExitStack
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import struct
import subprocess
import sys
import tempfile
import time

from separate_compilation import cgroup_record, sha

ROOT = Path(__file__).resolve().parents[1]
ALIAS = "large"
LARGE_BYTES = 700
RESULT_BYTES = 753
REQUIRED = 784
REQUEST = struct.pack("<QQQ", 1, 1, 5) + b"large"
RESULT_BODY = (struct.pack("<QQ", 1, 5) + b"large" + struct.pack("<QQ", 5, LARGE_BYTES)
               + b"R" * LARGE_BYTES + struct.pack("<QQQ", 1, 42, 0))
MAGIC = 0x44534F52564D5755
HEADER = struct.Struct("<22Q")
IDS = [bytes([value]) + bytes(15) for value in range(1, 6)]
CONTRACT = hashlib.sha256(b"wros-as-driver-result-retry.parameter.get").digest()


def encode_request(deadline):
    body = struct.pack("<QQQ", 1, deadline, len(REQUEST)) + REQUEST
    return body


def large_source(deadline):
    """@brief Stage a small ROS parameter.get request and verify the large reply."""
    request = encode_request(deadline)
    writes = [f"writeByte({offset}, {value});" for offset, value in enumerate(request)]
    source = """import { writeByte, writeWord, open, opened, connect, submit, result, resultWithCapacity,
    disconnect, replySize, replyRequired, clearReply, readWord } from "./wros";
const REQUIRED: u32 = 784;
const RESULT_BYTES: u32 = 753;
function stageRequest(): void {
""" + "\n".join(writes) + """
}
export function _start(): void {
    writeWord(0, 0x656772616c); // "large"
    if (open(5) != 0) unreachable();
    const handle = opened();
    let status: u32 = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = connect(handle);
    if (status != 0) unreachable();
    stageRequest();
    status = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = submit(handle, REQUEST_BYTES);
    if (status != 0) unreachable();
    if (result(handle, 1) != 90 || replySize() != 0 || replyRequired() != REQUIRED) unreachable();
    if (resultWithCapacity(handle, 1, REQUIRED - 1) != 90 ||
        replySize() != 0 || replyRequired() != REQUIRED) unreachable();
    status = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) {
        status = resultWithCapacity(handle, 1, REQUIRED);
    }
    if (status != 0 || replyRequired() != 0 || replySize() != 769) unreachable();
    if (readWord(0) != 0 || readWord(8) != RESULT_BYTES || readWord(16) != 1) unreachable();
    if (readWord(24) != 5 || readWord(37) != 5 || readWord(45) != 700) unreachable();
    if (readWord(53) != 0x5252525252525252 || readWord(741) != 0x5252525252525252) unreachable();
    if (readWord(753) != 1 || readWord(761) != 42) unreachable();
    clearReply();
    if (replySize() != 0 || replyRequired() != 0 || readWord(0) != 0) unreachable();
    if (resultWithCapacity(handle, 1, REQUIRED) != 11 || replySize() != 0) unreachable();
    if (disconnect(handle) != 0) unreachable();
}
"""
    return source.replace("const REQUIRED: u32",
                          f"const REQUEST_BYTES: u32 = {len(request)};\nconst REQUIRED: u32")


def parse_header(packet):
    if len(packet) < HEADER.size:
        raise ValueError("short authenticated driver packet")
    fields = list(HEADER.unpack_from(packet))
    body = packet[HEADER.size:]
    if (fields[0], fields[1], fields[3]) != (MAGIC, HEADER.size, 0) or fields[20] != len(body):
        raise ValueError("invalid authenticated driver header")
    return fields, body


def driver_worker(fd, peer_key, library, vm_source):
    """@brief Authenticate one VM and return exactly one oversized schema result."""
    sys.path.insert(0, str(Path(vm_source) / "test/0084.ros-runtime"))
    from attachment_peer import SecurePeer

    binding = b"".join(IDS) + CONTRACT
    expected_vm = int(sys.stdin.readline())
    peer = SecurePeer(Path(library), fd, peer_key, expected_vm, 1, binding, 176 + 4096)
    submitted = 0
    received_bytes = 0
    try:
        hello, body = parse_header(peer.recv())
        assert hello[2] == 1 and not body and hello[18:22] == [0, 0, 0, 0]
        hello[2] = 2
        peer.sendall(HEADER.pack(*hello))

        request, body = parse_header(peer.recv())
        assert request[2] == 3 and request[18] == 1 and request[21] == 0
        assert body == encode_request(request[19])
        submitted += 1

        result = list(request)
        result[2] = 4
        result[20] = len(RESULT_BODY)
        result[21] = 0
        peer.sendall(HEADER.pack(*result) + RESULT_BODY)
        received_bytes = len(RESULT_BODY)

        release, body = parse_header(peer.recv())
        assert release[2] == 5 and not body
    finally:
        peer.close()
    print(json.dumps({"authenticated": True, "submit_packets": submitted,
                      "response_bytes": received_bytes}), flush=True)


def build_peer(vm_source, ssl, output):
    """@brief Build the existing test-only TLS peer adapter."""
    command = [
        "/usr/bin/clang++-22", "-std=c++23", "-O3", "-g", "-Wall", "-Wextra", "-Werror",
        "-pthread", "-DUWVM_ROS_ATTACHMENT_OPENSSL", "-I" + str(ssl / "include"),
        "-I" + str(vm_source / "src"), "-isystem", str(vm_source / "third-parties/fast_io/include"),
        vm_source / "test/0084.ros-runtime/attachment_peer.cpp",
        ssl / "libssl.a", ssl / "libcrypto.a", "-ldl", "-shared", "-fPIC", "-o", output,
    ]
    subprocess.run(command, check=True, timeout=180)
    return command


def main():
    """@brief Run the exact selected wras frontend against the mutually authenticated VM channel."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("vm-source", "runtime", "openssl-root", "output"):
        parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
    args = parser.parse_args()
    if not __debug__:
        parser.error("qualification requires Python assertions")
    cgroup = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    args.output.mkdir(mode=0o700)
    sys.path.insert(0, str(args.vm_source / "test/0084.ros-runtime"))
    from attachment_peer import issue

    result_record = {"complete": False, "sdk_commit": args.commit, "vm_sha256": sha(args.runtime),
                     "cgroup": cgroup, "large_value_bytes": LARGE_BYTES,
                     "schema_body_bytes": RESULT_BYTES, "driver_wire_bytes": 16 + RESULT_BYTES,
                     "declared_response_bytes": 768, "emsgsize_required_bytes": REQUIRED,
                     "submit_expected": 1, "cases": []}

    def save():
        temporary = args.output / "results.pending"
        temporary.write_text(json.dumps(result_record, indent=2) + "\n")
        temporary.replace(args.output / "results.json")

    peer_library = args.output / "attachment-peer.so"
    result_record["peer_build_argv"] = build_peer(args.vm_source, args.openssl_root, peer_library)
    result_record["peer_library_sha256"] = sha(peer_library)
    with tempfile.TemporaryDirectory(dir=args.output) as work:
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("UWVM_", "WROS_", "XMAKE_"))}
        env.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=work)
        installed = subprocess.run([
            sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
            "--local-repository", ROOT, "--commit", args.commit, "--platform", "unitree",
            "--language", "as", "--prefix", work, "--", "--component", "development",
        ], cwd=ROOT, env=env, text=True, capture_output=True, timeout=180, check=True)
        install_record = json.loads(installed.stdout)
        sdk = Path(install_record["directory"])
        app = args.output / "controller.ts"
        deadline = time.monotonic_ns() + 30_000_000_000
        app.write_text(large_source(deadline))
        wasm = args.output / "controller.wasm"
        build = [sdk / "bin/wras", app, "--ros-driver", "--build-receipt", "-g",
                 *sum((["--ros-operation", name] for name in (
                     "capability.open", "capability.close", "driver.connect", "driver.submit",
                     "driver.result", "driver.disconnect")), []), "-o", wasm]
        built = subprocess.run(list(map(str, build)), cwd=ROOT, env=env,
                               capture_output=True, timeout=120)
        (args.output / "build.log").write_bytes(built.stdout + built.stderr)
        if built.returncode:
            raise RuntimeError((args.output / "build.log").read_text(errors="replace")[-3000:])
        evidence = json.loads(wasm.with_suffix(".wasm.wros-as.json").read_bytes())
        assert evidence["mte_requested"] and evidence["linear_memories"] == 1
        result_record.update(
            sdk_commit=install_record["commit"],
            install_packages=install_record["packages"],
            wras_sha256=sha(sdk / "bin/wras"),
            source_sha256=sha(app),
            wasm_sha256=sha(wasm),
            wasm_bytes=wasm.stat().st_size,
            build_receipt=evidence,
            build_argv=list(map(str, build)),
        )

        for engine in ("int", "aot"):
            with ExitStack() as resources:
                left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                for endpoint in (left, right):
                    endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
                resources.callback(left.close)
                resources.callback(right.close)
                vm_key, peer_key = issue(resources)
                peer = subprocess.Popen(
                    [sys.executable, "-B", Path(__file__), "--worker", str(right.fileno()),
                     str(peer_key), str(peer_library), str(args.vm_source)],
                    cwd=args.vm_source / "test/0084.ros-runtime", pass_fds=(right.fileno(), peer_key),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                right.close()
                clock = os.open(f"/proc/{peer.pid}/ns/time", os.O_RDONLY | os.O_CLOEXEC)
                resources.callback(os.close, clock)
                local_ns, peer_ns = os.stat("/proc/self/ns/time"), os.fstat(clock)
                assert (local_ns.st_dev, local_ns.st_ino) == (peer_ns.st_dev, peer_ns.st_ino)

                operations = ("capability.open", "capability.close", "driver.connect",
                              "driver.submit", "driver.result", "driver.disconnect")
                args_vm = [
                    args.runtime, "-WF3", "--runtime-" + engine, "--runtime-compile-threads", "0",
                    "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                    "--debug-fault-action", "exit", "--wasm-set-main-module-name", "main",
                    "--wasip1-single-create", "main", "--wasip1-single-disable", "main",
                    "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                ]
                for operation in operations:
                    args_vm.extend(["--ros-scene-interface", "robot", operation, "allow"])
                args_vm.extend([
                    "--ros-scene-grant", "robot", ALIAS, "driver", "param-lookup",
                    "registered-driver", "driver.connect,driver.submit,driver.result,driver.disconnect",
                    "--ros-scene-driver-budget", "robot", "1", "65536",
                    "--ros-scene-driver-channel", "robot", ALIAS, "main", str(left.fileno()),
                    str(peer.pid), str(os.getuid()), str(os.getgid()), *[item.hex() for item in IDS],
                    CONTRACT.hex(), "4096", "768", "30000000000", str(deadline + 1_000_000_000),
                    str(vm_key), str(clock),
                    "--ros-scene-driver-schema", "robot", ALIAS, "parameter.get", "32", "1024", "8",
                    "--ros-scene", "robot", "platform_extension",
                    "uwvm_ros_v2.platform_extension.unitree.v1", "enable",
                    "--ros-scene", "robot", "platform_extension.bind",
                    "uwvm_ros_v2.platform_extension.unitree.v1", ALIAS,
                    "--run", wasm,
                ])
                process = subprocess.Popen(args_vm, pass_fds=(left.fileno(), vm_key, clock),
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                left.close()
                peer.stdin.write((str(process.pid) + "\n").encode())
                peer.stdin.close()
                vm_stdout, vm_stderr = process.communicate(timeout=60)
                peer_stdout, peer_stderr = peer.communicate(timeout=15)
                (args.output / (engine + ".vm.stdout")).write_bytes(vm_stdout)
                (args.output / (engine + ".vm.stderr")).write_bytes(vm_stderr)
                (args.output / (engine + ".peer.stdout")).write_bytes(peer_stdout)
                (args.output / (engine + ".peer.stderr")).write_bytes(peer_stderr)
                assert process.returncode == 0, (engine, process.returncode, vm_stderr[-3000:])
                assert peer.returncode == 0, (engine, peer.returncode, peer_stderr[-3000:])
                observed = json.loads(peer_stdout)
                assert observed == {"authenticated": True, "submit_packets": 1,
                                    "response_bytes": RESULT_BYTES}
                result_record["cases"].append({
                    "engine": engine, "vm_exit": process.returncode,
                    "peer_exit": peer.returncode, "peer_observation": observed,
                    "host_request_count": observed["submit_packets"],
                    "emsgsize_attempts": [512, REQUIRED - 1, REQUIRED],
                    "delivered_result_bytes": 16 + RESULT_BYTES,
                })
                save()
    result_record["complete"] = True
    save()
    print(json.dumps(result_record, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--worker":
        driver_worker(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5])
    else:
        main()

