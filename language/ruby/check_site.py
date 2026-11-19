"""@file check_site.py
@brief Admit an installed mruby compiler only with its exact signed C profile.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from local_release import parse_site, verified_releases
from qualification import check_site, select_site_release


def main():
    """@brief Require the size, exception, thread and optimization settings used by wrrb."""
    data = sys.stdin.buffer.read(32769)
    digest = check_site(data, ROOT, "c")
    site = parse_site(data)
    row = select_site_release(verified_releases(site["trust"]), "c", digest)
    profile = Profile(row["profile"]["address_bits"])
    if row["profile"] != profile.to_dict() or row["settings"] != {"optimization": "3", "debug": True}:
        raise ValueError("mruby requires a signed Core 3.0 C site with EH, MTE, -O3 -g and one thread")
    print(digest)


if __name__ == "__main__":
    main()
