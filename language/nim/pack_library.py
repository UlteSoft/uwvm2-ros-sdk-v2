"""Derive the selective Nim guest library payload from the pinned upstream source distribution."""
import argparse
import hashlib
import io
import tarfile
from pathlib import Path
from build_producer import ARCHIVE, PIN


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    with ARCHIVE.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != PIN:
            raise ValueError("upstream Nim source digest mismatch")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r|xz") as source, tarfile.open(output, "x:xz", preset=6) as dest:
            for member in source:
                if member.isfile() and member.name.startswith("nim-2.2.4/lib/"):
                    contents = source.extractfile(member).read()
                    entry = tarfile.TarInfo(member.name)
                    entry.size = len(contents)
                    entry.mode = 0o644
                    dest.addfile(entry, io.BytesIO(contents))


if __name__ == "__main__":
    main()
