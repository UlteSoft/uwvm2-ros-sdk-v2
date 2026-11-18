"""Create a deterministic static library from matching WROS Wasm objects."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
import artifacts
from compiler import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("objects", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        if len(args.objects) > artifacts.MAX_MEMBERS:
            raise ValueError("too many archive objects")
        paths = [p.resolve(strict=True) for p in args.objects]
        if args.output.resolve() in paths:
            raise ValueError("output aliases an input")
        compiler_sha256 = digest(args.toolchain.resolve() / "bin/clang")
        members, total, profile, closure = [], 0, None, None
        for path in paths:
            data = artifacts.read_bounded(path)
            total += len(data) + 60
            if total > artifacts.MAX_BYTES:
                raise ValueError("archive objects exceed 128 MiB")
            note = artifacts.check_object(data, profile, compiler_sha256, closure)
            profile, closure = note["profile"], note["closure_sha256"]
            members.append(data)
        with tempfile.TemporaryDirectory(dir=args.output.parent) as directory:
            work = Path(directory)
            staged = work / "library.a"
            artifacts.archive(args.toolchain, staged, members, work / "objects")
            # Bound index overhead too, and check the generated container.
            if artifacts.archive_members(artifacts.read_bounded(staged)) != members:
                raise ValueError("archiver changed object members")
            os.replace(staged, args.output)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    return 0
