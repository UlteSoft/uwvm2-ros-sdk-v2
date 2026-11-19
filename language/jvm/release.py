"""Verify an operator-reviewed single-thread TeaVM release and its C memory backend."""
from pathlib import Path
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
import local_release
import qualification
from compiler import make_command, digest
from guest_profile import Profile

COMMANDS = {"java": "wrjava", "kotlin": "wrkt"}
PROFILE = Profile()
SETTINGS = {"optimization": "3", "debug": True}
FORMAT = "wros-jvm-synchronous-release-v1"
CASES = {"compile", "compile-observer", *(engine + "-" + case for engine in ("int", "aot")
         for case in ("hidden", "source", "owners", "owners-disabled"))}
canon = qualification.canonical


def bundle_at(toolchain, language):
    return (toolchain / "libexec/wros/jvm" / language).resolve(strict=True)


def host_files(bundle, language):
    """Hash the exact allowlisted JDK, class path and Linux x86-64 runtime.

    Refuse extra files in the compiler search roots and the global preload
    facility. The actual JVM subprocess uses these same library directories.
    """
    inventory = qualification.read_json(SDK / "language" / language / "host-inputs.json", 2 << 20)["files"]
    if ":" in str(bundle) or "\n" in str(bundle):
        raise ValueError("JVM bundle cannot contain search-path separators")
    expected = {r["path"]:r for r in inventory}
    if len(expected) != len(inventory):
        raise ValueError("ambiguous JVM compiler inventory")
    actual = {}
    for p in sorted(bundle.rglob("*")):
        if p.is_symlink():
            raise ValueError("symbolic links are outside the reviewed JVM bundle")
        if p.is_dir():
            continue
        key = p.relative_to(bundle).as_posix()
        row = expected.get(key)
        if not row or not p.is_file() or p.stat().st_size != row["bytes"] or digest(p) != row["sha256"]:
            raise ValueError("JVM host input differs: " + key)
        actual[key] = row["sha256"]
    if actual.keys() != expected.keys():
        raise ValueError("incomplete JVM compiler bundle")
    preload = Path("/etc/ld.so.preload")
    loader = Path("/lib64/ld-linux-x86-64.so.2")
    if (preload.exists() and preload.read_text().strip()) or digest(loader) != actual["lib/host-runtime/ld-linux-x86-64.so.2"]:
        raise ValueError("JVM system loader differs from the reviewed runtime")
    return canon(actual)


def measure(toolchain, sysroots, language):
    if language not in COMMANDS or len(sysroots) != 1:
        raise ValueError("the JVM release requires Java or Kotlin with exactly one wasm32 sysroot")
    _, rec = make_command(toolchain, sysroots, PROFILE, "c", ["-c"], verify=True)
    sources = (*qualification.COMMON, "install/private_exports.py", "include/wros/scene.h", "language/jvm",
               "third-parties/jvm", "bin/" + COMMANDS[language], "language/" + language)
    return {"host":host_files(bundle_at(toolchain, language), language),
            "sdk":canon({p:qualification.files(SDK / p) for p in sources}),
            "backend":{"compiler":rec["compiler_sha256"], "sysroot":rec["closure_sha256"],
                       "linker":digest(toolchain / "bin/wasm-ld"), "archiver":digest(toolchain / "bin/llvm-ar")}}


def c_parent(rows, parent_digest, measured):
    matches = [r for r in rows if isinstance(r, dict) and r.get("language") == "c" and canon(r) == parent_digest]
    if len(matches) != 1:
        raise ValueError("the JVM site requires its exact approved C release")
    row = matches[0]
    if (not qualification.complete_release(row) or row["profile"] != PROFILE.to_dict()
            or row["settings"] != SETTINGS or any(row["inputs"].get(k) != v for k, v in measured.items())):
        raise ValueError("C memory backend differs from the signed JVM release")
    return row


def authorize(site, language):
    if not site:
        raise ValueError("no signed strict synchronous JVM installation; provide --site-profile at installation")
    rows = local_release.verified_releases(site["trust"])
    selection = site.get("release_sha256")
    matches = [r for r in rows if isinstance(r, dict) and r.get("language") == language and r.get("format") == FORMAT
               and (selection is None or canon(r) == selection)]
    if len(matches) != 1:
        raise ValueError("the site needs exactly one signed synchronous " + language + " release")
    row = matches[0]
    if (row.get("profile") != PROFILE.to_dict() or row.get("settings") != SETTINGS
            or set(row.get("evidence", {})) != CASES or not all(isinstance(v, str) and qualification.HEX.fullmatch(v)
            for v in row["evidence"].values())):
        raise ValueError("incomplete JVM ownership qualification")
    tc = Path(site["toolchain"]).resolve(strict=True)
    sysroots = [Path(p).resolve(strict=True) for p in site["sysroots"]]
    measured = measure(tc, sysroots, language)
    parent = c_parent(rows, row.get("c_release_sha256"), measured["backend"])
    if row.get("inputs") != measured or row.get("vm_sha256") != parent["vm_sha256"]:
        raise ValueError("JVM compiler, collector, sysroot or VM differs from the approved release")
    return row, tc, sysroots[0], bundle_at(tc, language)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("select java or kotlin")
    row, *_ = authorize(local_release.parse_site(sys.stdin.buffer.read(32769)), sys.argv[1])
    print(canon(row))
