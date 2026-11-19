"""Bind a Rust no_std installation to a signed release and its pinned tools."""
from argparse import Namespace
import json
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
from guest_profile import Profile
import local_release
import qualification


def inputs(toolchain):
    root = toolchain / "libexec/wros"
    return {"rustc": root / "rust/bin/rustc", "host_cxx": root / "rust-host/c++"}


def select(site):
    rows = local_release.verified_releases(site["trust"])
    row = qualification.select_site_release(rows, "rs", site.get("release_sha256"))
    if (row["profile"] != Profile(32, exceptions="noeh").to_dict()
            or row["settings"] != {"optimization": "3", "debug": True}):
        raise ValueError("Rust site requires wasm32 Core 3.0, single-threaded panic=abort at -O3 -g")
    return row


def verify(data):
    site = local_release.parse_site(data)
    row = select(site)
    options = Namespace(toolchain=Path(site["toolchain"]), sysroots=list(map(Path, site["sysroots"])))
    extra = inputs(options.toolchain)
    actual = qualification.measure_inputs("rs", options, Profile(32, exceptions="noeh"), extra, sdk=SDK, candidates=[row])
    if actual != row["inputs"]:
        raise ValueError("Rust site inputs differ from the signed release")
    rustroot = extra["rustc"].parents[1].resolve(strict=True)
    lock = json.loads((SDK / "language/rust/toolchain-inputs.json").read_text())
    for relative, expected in lock["host_files"].items():
        source = (rustroot / relative).resolve(strict=True)
        if not source.is_relative_to(rustroot) or qualification.digest(source) != expected:
            raise ValueError("Rust host component differs from the SDK release: " + relative)
    return qualification.canonical(row)


if __name__ == "__main__":
    print(verify(sys.stdin.buffer.read(32769)))
