"""Test peer for the Objective-C platform route. Only hello and release are accepted."""
from pathlib import Path
import json
import os
import socket
import struct
import sys


def main():
    fixture, library, descriptor, key, mode = sys.argv[1:]
    sys.path.insert(0, str(Path(fixture).resolve()))
    from attachment_peer import SecurePeer
    from run_scene_vm import verify_gate

    verify_gate()
    pid = int(sys.stdin.readline())
    fd = int(descriptor)
    binding = b''.join(bytes([n])+bytes(15) for n in range(1,6))+bytes(range(1,33))
    if mode == "enabled":
        channel = SecurePeer(library, fd, int(key), pid, 1, binding, 176+128)
        try:
            for expected in (1, 5):
                frame = channel.recv()
                expected_header = struct.pack('<4Q', 0x44534f52564d5755, 176, expected, 0)
                assert frame == expected_header + binding + bytes(32)
                if expected == 1:
                    channel.sendall(struct.pack('<4Q', 0x44534f52564d5755, 176, 2, 0) + binding + bytes(32))
        finally:
            channel.close()
    else:
        with socket.socket(fileno=fd) as raw:
            raw.settimeout(15)
            assert raw.recv(1) == b'', "denied route transmitted bytes to the driver"
    print(json.dumps({"packets": 2 if mode == "enabled" else 0, "effects": 0}), flush=True)


if __name__ == "__main__":
    main()
