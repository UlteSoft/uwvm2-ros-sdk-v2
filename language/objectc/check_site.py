"""Verify a site's Wasm Objective-C compiler and GNUstep runtime against its signed release."""
from argparse import Namespace
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SDK / "install"), str(SDK / "language/objectc")]
from compiler import make_command
from guest_profile import Profile
import local_release
import qualification
import runtime


def verify(data):
    site = local_release.parse_site(data)
    releases = local_release.verified_releases(site["trust"])
    row = qualification.select_site_release(releases, "objectc", site.get("release_sha256"))
    options = Namespace(toolchain=Path(site["toolchain"]), sysroots=list(map(Path, site["sysroots"])))
    profile = Profile(**{key: row["profile"][key] for key in Profile.__dataclass_fields__})
    _, record = make_command(options.toolchain, options.sysroots, profile, "c", ["-c"], verify=True)
    extra = runtime.verified_inputs(options.toolchain, profile, record)
    if qualification.measure_inputs("objectc", options, profile, extra, sdk=SDK, candidates=[row]) != row["inputs"]:
        raise ValueError("Objective-C SDK, compiler or runtime differs from the signed release")
    return qualification.canonical(row)


if __name__ == "__main__":
    print(verify(sys.stdin.buffer.read(32769)))
