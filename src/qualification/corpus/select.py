#!/usr/bin/env python3
"""Select a reproducible 300-package review cohort from the ROS capability inventory."""
import argparse
import hashlib
import json
import re
from pathlib import Path

INVENTORY_SHA256 = "66a768aca13d6ccd973348416cbaa25346111ea5fd8c666e8dc2830d68990714"
ANCHORS = ("angles", "rcutils", "rosidl_runtime_c", "tf2")
SEED = "uwrosv2-port-cohort-1"


def rank(value):
    return hashlib.sha256(f"{SEED}\0{value}".encode()).digest()


def select(path):
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != INVENTORY_SHA256:
        raise ValueError("inventory digest mismatch")
    packages = {row["name"]: row["instances"] for row in json.loads(contents)}
    eligible = {}
    for name, rows in packages.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
            continue
        candidates = [row for row in rows if row.get("source_url", "").startswith("https://")
                      and re.fullmatch("[a-f0-9]{64}", row.get("archive_sha256", ""))]
        if candidates:
            eligible[name] = min(candidates, key=lambda row: (rank(row["source_id"]), row["manifest"]))
    names = list(ANCHORS) + sorted(eligible.keys() - set(ANCHORS), key=rank)[:300-len(ANCHORS)]
    return [{"package": name, **eligible[name]} for name in names]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages_json", type=Path)
    print(json.dumps(select(parser.parse_args().packages_json), indent=2, ensure_ascii=False))
