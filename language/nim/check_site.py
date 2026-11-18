"""Bind a selected Nim installation to its signed frontend, backend and sysroot."""
from argparse import Namespace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
import local_release
import qualification


def main():
    site = local_release.parse_site(sys.stdin.buffer.read(32769))
    rows = local_release.verified_releases(site["trust"])
    row = qualification.select_site_release(rows, "nim", site.get("release_sha256"))
    options = Namespace(toolchain=Path(site["toolchain"]), sysroots=list(map(Path, site["sysroots"])))
    profile = Profile(**{key: row["profile"][key] for key in Profile.__dataclass_fields__})
    producer = options.toolchain / "bin/wrnim-lower"
    measured = qualification.measure_inputs("nim", options, profile, {"producer": producer}, sdk=ROOT, candidates=[row])
    if measured != row["inputs"]:
        raise ValueError("installed Nim inputs differ from the approved release")
    print(qualification.canonical(row))


if __name__ == "__main__":
    main()
