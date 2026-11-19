"""Authenticate a site-specific Zig frontend, WasmMTE backend and VM."""
import hashlib
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))

from artifacts import validate_profile
from compiler import digest, make_command
from guest_profile import Profile
import local_release
import qualification

VERSION = "0.16.0"
PRODUCER = "zig-x86_64-linux-" + VERSION
ARCHIVE = PRODUCER + ".tar.xz"
ARCHIVE_SIZE = 55478392
ARCHIVE_SHA256 = "70e49664a74374b48b51e6f3fdfbf437f6395d42509050588bd49abe52ba3d00"
FORMAT = "wros-zig-freestanding-release-v1"
BUILD = "wros-zig-freestanding-build-v1"
TESTS = {"vm-int", "vm-aot", "storage", "authority", "admission"}
SETTINGS = {"optimization": "3", "debug": True}
FILES = (*qualification.COMMON, "bin/wrzig", "language/zig")


def archive_path(toolchain):
    return toolchain / "share/wros/zig" / ARCHIVE


def producer_archive(toolchain):
    data = local_release.read_file(archive_path(toolchain), ARCHIVE_SIZE)
    if len(data) != ARCHIVE_SIZE or hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("the local Zig archive differs from the official pinned release")
    return data


def marker_path(toolchain):
    return toolchain / "bin/wros-zig-mte"


def profile_for(bits, tagged=True):
    return Profile(bits, mte=tagged, exceptions="noeh")


def measure(toolchain, sysroots, profile):
    """Measure the files authorized to produce the reviewed guest profile."""
    if profile != profile_for(profile.address_bits):
        raise ValueError("the Zig release only covers tagged freestanding storage")
    producer_archive(toolchain)
    marker = marker_path(toolchain)
    _, closure = make_command(toolchain, sysroots, profile, "c", ["-c"], verify=True)
    return {
        "zig_archive": ARCHIVE_SHA256,
        "marker": digest(marker),
        "compiler": closure["compiler_sha256"],
        "sysroot": closure["closure_sha256"],
        "wasm_ld": digest(toolchain / "bin/wasm-ld"),
        "sdk": qualification.canonical({path: qualification.files(SDK / path) for path in FILES}),
    }


def authorized(site, bits=None):
    """Require one signed row for the exact source driver and toolchain."""
    if site is None:
        raise ValueError("wrzig defaults to WasmMTE and needs a signed Zig site profile")
    rows = local_release.verified_releases(site["trust"])
    matches = [r for r in rows if isinstance(r, dict) and r.get("format") == FORMAT
               and r.get("language") == "zig"
               and ("release_sha256" not in site or qualification.canonical(r) == site["release_sha256"])]
    if len(matches) != 1:
        raise ValueError("the site needs exactly one matching signed Zig release")
    row = matches[0]
    if set(row) != {"format", "language", "profile", "settings", "inputs", "vm_sha256", "tests"}:
        raise ValueError("unexpected signed Zig release fields")
    fields = validate_profile(row["profile"])
    profile = Profile(**{name: fields[name] for name in Profile.__dataclass_fields__})
    if profile != profile_for(profile.address_bits) or (bits is not None and bits != profile.address_bits):
        raise ValueError("requested Zig profile differs from the signed address width")
    if (not isinstance(row["tests"], dict) or set(row["tests"]) != TESTS or row["settings"] != SETTINGS
            or not all(isinstance(value, str) and qualification.HEX.fullmatch(value)
                       for value in [row["vm_sha256"], *row["tests"].values()])):
        raise ValueError("the Zig release has incomplete or invalid qualification evidence")
    toolchain = Path(site["toolchain"]).resolve(strict=True)
    sysroots = list(map(Path, site["sysroots"]))
    if row["inputs"] != measure(toolchain, sysroots, profile):
        raise ValueError("Zig tools, SDK or code-generation inputs differ from the signed release")
    return row, profile, toolchain, sysroots


def receipt(row, profile, source_sha256):
    result = {"format": BUILD, "language": "zig", "settings": SETTINGS, "profile": profile.to_dict(),
              "mode": "strict" if row is not None else "off", "source_sha256": source_sha256}
    if row is not None:
        result.update(release_sha256=qualification.canonical(row), vm_sha256=row["vm_sha256"])
    return result
