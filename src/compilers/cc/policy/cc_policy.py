"""Admission, object sealing and publication for the native wrc and wrcc drivers."""
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compiler import digest
from frontend import main


def run():
    language, descriptor = sys.argv[1:3]
    if language not in ("c", "cpp"):
        raise ValueError("expected c or cpp")
    program = "wrcc" if language == "cpp" else "wrc"
    sys.argv = [program, *sys.argv[3:]]
    executable = Path("/proc") / str(os.getppid()) / "exe"
    with socket.socket(fileno=int(descriptor)) as channel:
        def compile_native(command, compiler_sha256):
            # The compiler process owns the driver and runs cc1. An explicit
            # site may select a different ELF whose digest was just admitted.
            mode = b"embedded" if digest(executable) == compiler_sha256 else b"external"
            if mode == b"embedded":
                # A multi-job Clang driver can launch cc1 separately. Preserve
                # its qualified clang/clang++ path when it creates that job.
                command = [command[0], "-no-canonical-prefixes", *command[1:]]
            packet = b"\0".join([mode, *map(os.fsencode, command)]) + b"\0"
            if len(packet) > 8 * 1024 * 1024:
                raise ValueError("native compilation command exceeds the SDK bound")
            channel.sendall(struct.pack("!I", len(packet)) + packet)
            with channel.makefile("rb") as stream:
                status = stream.read(4)
            if len(status) != 4:
                raise ValueError("native compiler exited before reporting its result")
            code, = struct.unpack("!I", status)
            if code:
                raise subprocess.CalledProcessError(code, command)
        return main(language, compile_native)


if __name__ == "__main__":
    raise SystemExit(run())
