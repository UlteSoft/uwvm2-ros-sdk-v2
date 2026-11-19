"""Select and verify the TinyGo producer recorded in a local signed site statement."""
from argparse import Namespace
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
from guest_profile import Profile
import local_release
import qualification


def inputs(toolchain):
    root = toolchain / "libexec/wros"
    return {"go": root / "go/bin/go", "tinygo": root / "tinygo/bin/tinygo",
            "host_cxx": root / "host-cxx"}


def select(site):
    rows = local_release.verified_releases(site["trust"])
    row = qualification.select_site_release(rows, "tinygo", site.get("release_sha256"))
    profile = Profile(**{key: row["profile"][key] for key in Profile.__dataclass_fields__})
    if (profile.address_bits != 32 or profile.threads or profile.wasm_version != "3.0"
            or row["settings"] != {"optimization": "3", "debug": True}):
        raise ValueError("the TinyGo producer requires single-threaded wasm32/3.0 at -O3 -g")
    return row


def verify(data):
    site = local_release.parse_site(data)
    row = select(site)
    options = Namespace(toolchain=Path(site["toolchain"]), sysroots=list(map(Path, site["sysroots"])))
    profile = Profile(**{key: row["profile"][key] for key in Profile.__dataclass_fields__})
    actual = qualification.measure_inputs("tinygo", options, profile, inputs(options.toolchain), sdk=SDK, candidates=[row])
    if actual != row["inputs"]:
        raise ValueError("TinyGo site compiler or SDK differs from the signed release")
    return qualification.canonical(row)


if __name__ == "__main__":
    print(verify(sys.stdin.buffer.read(32769)))
