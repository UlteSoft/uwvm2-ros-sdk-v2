"""Verify one selected ROS package resource and generate the guest's immutable input."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/migration"))
from package_resources import collect, unique_fields, write_pack


def publish(path, data):
    """@brief Atomically replace the header after publishing its immutable data file."""
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
        staged = Path(out.name)
    try:
        staged.write_bytes(data)
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def main():
    """@brief Pin the source package and resource before embedding either source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--platform-lock", type=Path, required=True)
    parser.add_argument("--package-root", type=Path)
    args = parser.parse_args()
    root = args.package_root
    lock = args.platform_lock
    if root is None:
        root = ROOT / "third-parties/migration-examples/sensor_msgs"
        lock = Path(__file__).with_name("imu.lock")
    with lock.open("rb") as stream:
        raw_lock = stream.read(4097)
    if len(raw_lock) > 4096:
        parser.error("resource lock exceeds 4096 bytes")
    entries = json.loads(raw_lock, object_pairs_hook=unique_fields)
    if not isinstance(entries, list) or len(entries) != 1:
        parser.error("the example requires exactly one pinned resource")
    rows = collect([root], entries, verify=True)
    selected, raw = rows[0]
    # The package verifier pins SHA-256. The smaller checksum also exercises all
    # bytes within the guest, where no filesystem or hash-provider access is needed.
    checksum = 2166136261
    for byte in raw:
        checksum = ((checksum ^ byte) * 16777619) & 0xffffffff
    pack = io.BytesIO()
    write_pack(pack, rows)
    data = pack.getvalue()
    filename = hashlib.sha256(data).hexdigest() + ".bin"
    header = (
        '/* Generated from the SHA-256-verified package resource. */\n'
        'static const unsigned char resource_pack[] = {\n'
        f'#embed "{filename}"\n'
        '};\n'
        f'static const char resource_uri[] = "{selected["uri"]}";\n'
        f'#define RESOURCE_SIZE {len(raw)}u\n'
        f'#define RESOURCE_CHECKSUM {checksum}u\n'
    )
    args.output.mkdir(parents=True, exist_ok=True)
    publish(args.output / filename, data)
    publish(args.output / "selected_resource.h", header.encode("ascii"))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(str(error))
