"""Pack one native Linux executable or shared library into a reproducible, independently verifiable tar.xz."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import runpy
import tarfile
import tempfile


INSTALLER = runpy.run_path(str(Path(__file__).resolve().parents[2] / "install/install.py"))


def file_hash(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1 << 20), b""):
            checksum.update(data)
    return checksum.hexdigest()


def package(executable, name, destination, *, host=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9+-]*", name):
        raise ValueError("invalid native program name")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with executable.open("rb") as source, tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        expected = host or INSTALLER["current_host"]()
        INSTALLER["require_host"](executable, expected)
        packed = Path(temp) / "program.tar.xz"
        with lzma.open(packed, "wb", format=lzma.FORMAT_XZ, preset=4) as encoded:
            with tarfile.open(fileobj=encoded, mode="w|", format=tarfile.USTAR_FORMAT) as archive:
                member = tarfile.TarInfo(name)
                member.mode = 0o755
                member.size = os.fstat(source.fileno()).st_size
                archive.addfile(member, source)
        checksum = hashlib.sha256()
        with tarfile.open(packed, "r|xz") as archive:
            member = archive.next()
            with archive.extractfile(member) as program:
                for data in iter(lambda: program.read(1 << 20), b""):
                    checksum.update(data)
            if member.name != name or archive.next() is not None:
                raise ValueError("invalid native program archive")
        entry = {"format": "tar.xz", "member": name, "compressed_bytes": packed.stat().st_size,
                 "compressed_sha256": file_hash(packed), "bytes": member.size, "sha256": checksum.hexdigest()}
        os.replace(packed, destination)
        return entry


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("executable", type=Path)
    cli.add_argument("--name", required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--host", choices=INSTALLER["HOSTS"], help="verify a cross-built target ABI")
    args = cli.parse_args()
    print(json.dumps(package(args.executable, args.name, args.output, host=args.host), indent=2))
