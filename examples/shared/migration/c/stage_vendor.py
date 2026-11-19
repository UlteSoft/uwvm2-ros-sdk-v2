"""@file stage_vendor.py
@brief Map one pinned local vendor resource into a named SDK-owned ROS package.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

SDK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SDK / "tools/migration"))
from package_resources import parts, read_file, unique_fields
from package_manifest import describe


def bounded(path):
    """@brief Read a single small example descriptor before parsing its contents."""
    with path.open("rb") as stream:
        data = stream.read(4097)
    if len(data) > 4096:
        raise ValueError("example descriptor exceeds 4096 bytes")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path, help="selected C migration project")
    parser.add_argument("--source-root", required=True, type=Path, help="locally supplied original vendor repository root")
    parser.add_argument("--output", required=True, type=Path, help="new ROS package directory")
    args = parser.parse_args()
    lock = json.loads(bounded(args.project / "upstream.lock"), object_pairs_hook=unique_fields)
    if not isinstance(lock, list) or len(lock) != 1 or not isinstance(lock[0], dict) or set(lock[0]) != {"uri", "sha256", "manifest_sha256"}:
        parser.error("expected one pinned package URI")
    entry = lock[0]
    package, path = parts(entry["uri"])
    if path[0] in ("package.xml", "manifest.xml"):
        parser.error("vendor resource collides with its package manifest")
    manifest = bounded(args.project / "vendor-package.xml")
    if not package.startswith("wros_example_") or not manifest or len(manifest) > 4096:
        parser.error("expected an SDK example package manifest")
    parsed = describe(manifest, "package.xml", package)
    if parsed["name"] != package or parsed["sha256"] != entry["manifest_sha256"]:
        parser.error("mapped package manifest differs from its lock")
    fd = os.open(args.source_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        raw = read_file(fd, path, 1024 * 1024)
    finally:
        os.close(fd)
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        parser.error("vendor resource differs from its lock")
    # Claim a fresh destination. Never replace a prior package or edit the source.
    args.output.mkdir(mode=0o700)
    try:
        (args.output / "package.xml").write_bytes(manifest)
        dest = args.output.joinpath(*path)
        dest.parent.mkdir(exist_ok=True, parents=True)
        dest.write_bytes(raw)
    except BaseException:
        shutil.rmtree(args.output)
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(str(error))
