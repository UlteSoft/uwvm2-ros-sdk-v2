"""@file check_site.py
@brief Verify the installed CPython runtime width against the signed C toolchain selection.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
import local_release
from qualification import check_site, select_site_release


def main():
    """@brief Authenticate the C release and require one selected Python target with the same pointer width."""
    data = sys.stdin.buffer.read(32769)
    digest = check_site(data, ROOT, "c")
    site = local_release.parse_site(data)
    row = select_site_release(local_release.verified_releases(site["trust"]), "c", digest)
    width = row["profile"]["address_bits"]
    directory = ROOT / "third-parties/cpython-runtime"
    records = list(directory.glob("*.json"))
    if len(records) != 1:
        raise ValueError("select one Python runtime target per installation")
    runtime = json.loads(records[0].read_bytes())
    if runtime.get("profile", {}).get("address_bits") != width:
        raise ValueError("Python runtime width differs from selected signed C site")
    print(digest)


if __name__ == "__main__":
    main()
