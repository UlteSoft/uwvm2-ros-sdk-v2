"""Pin and pack explicit ROS package:// resources for core Wasm guests."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
from urllib.parse import quote, unquote_to_bytes

from package_manifest import MAX_MANIFEST, describe

MAGIC = b"WROSRES\0"
MAX_TOTAL = 64 * 1024 * 1024
MAX_ENTRIES = 65535
MAX_URI = 1024


def parts(uri):
    if not isinstance(uri, str) or not uri.isascii() or len(uri) > MAX_URI:
        raise ValueError("invalid resource URI length or encoding")
    m = re.fullmatch(r"package://([a-zA-Z][a-zA-Z0-9_-]*)/(.+)", uri)
    if not m:
        raise ValueError("expected a package:// URI")
    segments = []
    for raw in m[2].split("/"):
        segment = unquote_to_bytes(raw).decode("utf-8")
        if (not segment or segment in (".", "..") or "/" in segment or "\\" in segment or
                any(ord(c) < 32 or ord(c) == 127 for c in segment) or quote(segment, safe="-._~") != raw):
            raise ValueError("noncanonical resource path: " + uri)
        segments.append(segment)
    return m[1], segments


def read_file(root_fd, segments, limit):
    """Open each component below the pinned root without following links."""
    directory = os.dup(root_fd)
    try:
        for segment in segments[:-1]:
            child = os.open(segment, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(segments[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                raise ValueError("resource is not a regular file within the byte budget")
            data = stream.read(before.st_size + 1)
            after = os.fstat(fd)
            if (len(data) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                    != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                raise ValueError("resource changed while being read")
            return data
    finally:
        os.close(directory)


@contextlib.contextmanager
def packages(roots):
    result = {}
    with contextlib.ExitStack() as opened:
        for path in roots:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            opened.callback(os.close, fd)
            try:
                filename = "package.xml"
                raw = read_file(fd, [filename], MAX_MANIFEST)
            except FileNotFoundError:
                filename = "manifest.xml"
                raw = read_file(fd, [filename], MAX_MANIFEST)
            info = describe(raw, filename, Path(path).resolve().name)
            name = info["name"]
            if name in result:
                raise ValueError("ambiguous package root for " + name)
            result[name] = (fd, info["sha256"])
        yield result


def collect(roots, entries, verify):
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("invalid number of resources")
    total = 16 + 16 * len(entries)
    keys = set()
    rows = []
    with packages(roots) as registered:
        for entry in entries:
            if verify and (not isinstance(entry, dict) or set(entry) != {"uri", "sha256", "manifest_sha256"}):
                raise ValueError("invalid resource lock entry")
            uri = entry["uri"] if verify else entry
            name, children = parts(uri)
            if uri in keys or name not in registered:
                raise ValueError("duplicate URI or unregistered package: " + uri)
            keys.add(uri)
            root_fd, manifest_hash = registered[name]
            total += len(uri)
            data = read_file(root_fd, children, MAX_TOTAL - total)
            total += len(data)
            locked = {"uri": uri, "sha256": hashlib.sha256(data).hexdigest(), "manifest_sha256": manifest_hash}
            if verify and entry != locked:
                raise ValueError("resource or package manifest does not match its lock: " + uri)
            rows.append((locked, data))
    return sorted(rows, key=lambda row: row[0]["uri"])


def write_pack(stream, rows):
    offset = 16 + 16 * len(rows)
    stream.write(struct.pack("<8sII", MAGIC, len(rows), offset))
    for entry, data in rows:
        n = len(entry["uri"])
        stream.write(struct.pack("<IIII", offset, n, offset+n, len(data)))
        offset += n + len(data)
    for entry, data in rows:
        stream.write(entry["uri"].encode("ascii"))
        stream.write(data)


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field in resource lock: " + key)
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    for mode in ("lock", "pack"):
        sub = commands.add_parser(mode)
        sub.add_argument("--package-root", action="append", type=Path, required=True)
        sub.add_argument("--output", type=Path, required=True)
        if mode == "lock":
            sub.add_argument("--uri", action="append", required=True)
        else:
            sub.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    temp = None
    try:
        if args.mode == "pack":
            with args.lock.open("rb") as stream:
                raw = stream.read(MAX_TOTAL + 1)
                if len(raw) > MAX_TOTAL:
                    raise ValueError("oversized resource lock")
            entries = json.loads(raw, object_pairs_hook=unique_fields)
        else:
            entries = args.uri
        rows = collect(args.package_root, entries, args.mode == "pack")
        with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as stream:
            temp = Path(stream.name)
            if args.mode == "pack":
                write_pack(stream, rows)
            else:
                stream.write((json.dumps([r[0] for r in rows], indent=2) + "\n").encode())
        temp.replace(args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
