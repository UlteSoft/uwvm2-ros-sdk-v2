"""Rebuild one release wrjava ELF with the pinned Zig 0.15.2 Linux x86-64 C toolchain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
TARGETS = {"linux-x86_64": ["x86_64-linux-musl"], "linux-i686": ["x86-linux-musl"],
           "linux-aarch64": ["aarch64-linux-musl"], "linux-arm": ["arm-linux-musleabi", "-mcpu=arm926ej_s"],
           "linux-armhf": ["arm-linux-musleabihf", "-mcpu=generic+v7a+vfp3d16"]}
ZIG_SHA256 = "2858dc89dbbfdd08cceda1b841e7fd0a793a1a67b49f150bc3d0d1de44ed7f51"


def rebuild(zig, host, output, work):
    with zig.open("rb") as file:
        if hashlib.file_digest(file, "sha256").hexdigest() != ZIG_SHA256:
            raise ValueError("expected the Linux x86-64 Zig 0.15.2 compiler from the locked distribution")
    work.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(dir=work.resolve()) as temp:
        scratch = Path(temp)
        program = scratch / "wrjava"
        env = dict(os.environ, TMPDIR=temp, ZIG_GLOBAL_CACHE_DIR=str(work.resolve() / "zig-cache"),
                   ZIG_LOCAL_CACHE_DIR=str(scratch / "zig-local"))
        subprocess.run([zig, "cc", "-target", *TARGETS[host], "-std=c11", "-Os", "-static", "-s",
                        "-Wl,--build-id=none", HERE / "driver/wrjava.c", "-o", program], check=True, env=env)
        pack = runpy.run_path(str(HERE.parent / "package_native.py"))["package"]
        row = pack(program, "wrjava", scratch / "wrjava.tar.xz", host=host)
        (scratch / "wrjava.tar.xz").replace(output)
        return row


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zig", required=True, type=Path)
    parser.add_argument("--host", required=True, choices=TARGETS)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(rebuild(args.zig.resolve(), args.host, args.output.resolve(), args.work), indent=2))
