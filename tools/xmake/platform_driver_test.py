"""@file platform_driver_test.py
@brief Exercise a selected platform's parent and child driver permission gates.
@details The peer is one end of a private socket pair. The test supplies no
device or routable address and treats any data sent to the peer as failure.
"""
from contextlib import ExitStack
import fcntl
import hashlib
import os
import socket
import subprocess
import time


def check(argv, module, platform):
    """@brief Run both denial configurations and verify an untouched external peer.
    @param argv Audited VM executable, engine, features and local clock grants.
    @param module Snapshot of the language-authored Wasm program.
    @param platform Exact installed platform identity validated by the caller.
    @return Zero when both guest assertions and external zero-byte checks pass.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
    for parent_allowed in (True, False):
        with ExitStack() as resources:
            client, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            for endpoint in (client, peer):
                resources.enter_context(endpoint)
                endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
            key = os.memfd_create("wros-test-session-key", os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
            resources.callback(os.close, key)
            local = Ed25519PrivateKey.generate().private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
            remote = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            if os.write(key, local + remote) != 64:
                raise OSError("incomplete test identity")
            fcntl.fcntl(key, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW |
                        fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
            clock = os.open("/proc/self/ns/time", os.O_RDONLY | os.O_CLOEXEC)
            resources.callback(os.close, clock)
            flags = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
            for operation in ("capability.open", "capability.close", "driver.connect", "driver.disconnect"):
                flags.extend(["--ros-scene-interface", "robot", operation, "allow"])
            actions = "driver.connect,driver.disconnect" if parent_allowed else "driver.disconnect"
            child = "uwvm_ros_v2.platform_extension." + platform + ".v1"
            identifiers = [os.urandom(16).hex() for _ in range(5)]
            contract = hashlib.sha256(b"SDK local driver permission example").hexdigest()
            deadline = time.monotonic_ns() + 660_000_000_000
            flags.extend(["--ros-scene-grant", "robot", "arm", "driver", "joint", "registered-driver", actions,
                          "--ros-scene-driver-budget", "robot", "1", "1048576",
                          "--ros-scene-driver-channel", "robot", "arm", "main", str(client.fileno()),
                          str(os.getpid()), str(os.getuid()), str(os.getgid()), *identifiers, contract,
                          "128", "128", "1000000000", str(deadline), str(key), str(clock),
                          "--ros-scene-driver-schema", "robot", "arm", "device.submit", "64", "64", "8",
                          "--ros-scene", "robot", "platform_extension", child, "disable" if parent_allowed else "enable",
                          "--ros-scene", "robot", "platform_extension.bind", child, "arm"])
            result = subprocess.run([*argv, *flags, "--run", str(module)], pass_fds=(client.fileno(), key, clock),
                                    timeout=600)
            if time.monotonic_ns() >= deadline:
                raise RuntimeError("test identity expired during the platform check")
            if result.returncode:
                return result.returncode if result.returncode > 0 else 128 - result.returncode
            peer.setblocking(False)
            try:
                peer.recv(1)
            except BlockingIOError:
                continue
            raise RuntimeError("driver permission test unexpectedly produced a peer event")
    return 0
