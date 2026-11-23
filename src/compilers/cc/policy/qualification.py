"""Admission of reviewed compiler/runtime combinations for managed memory lifetimes.

The release index belongs to the trusted, commit-pinned SDK installation.
A sysroot manifest describes its inputs; its self-reported qualification is
never authorization. Application source suppressions and custom pools remain
part of the separate artifact review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from compiler import compiler_environment, digest, make_command
import local_release
from artifacts import NOTE, read_bounded, sections, unique_object, validate_profile


ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("share/qualification/memory-neighbors.json")
LANGUAGES = {"c", "cpp"}
COMMON = (
    "install/qualification.py", "install/local_release.py", "install/artifacts.py", "install/compiler.py",
    "install/guest_profile.py", "install/imports.py", "install/frontend.py", "install/cc_policy.py",
    "install/portable_cc.py", "install/sysroot_layout.py", "share/abi/ros.json",
)
SDK_INPUTS = {"c": ("bin/wrc", "include/u2rosv2/universal/c"), "cpp": ("bin/wrcc", "include/u2rosv2/universal/c++")}
PROOFS = {"compiler-stack", "global-layout", "aggregate-pointers", "heap", "language", "vm-int", "vm-aot"}
MAX_RECEIPT_BYTES = 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")


def arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mte", dest="mte", action="store_true", help="enable WasmMTE instrumentation (default)")
    group.add_argument("--no-mte", dest="mte", action="store_false", help="use a matching uninstrumented sysroot")
    parser.set_defaults(mte=True)
    parser.add_argument("--require-qualified", "--strict-mte", action="store_true",
                        help="require a reviewed release of these exact tools, SDK, profile and deployment VM")
    parser.add_argument("--build-receipt", action="store_true", help="write OUTPUT.wros-build.json")


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def files(path):
    if path.is_file():
        return {"": digest(path)}
    if not path.is_dir():
        raise ValueError("qualification input missing: " + str(path))
    result = {}
    for file in sorted(path.rglob("*")):
        if "__pycache__" in file.parts or file.suffix == ".pyc":
            continue
        if file.is_symlink() and file.is_dir():
            raise ValueError("ambiguous subdirectory link in qualification input: " + str(file))
        if file.is_file():
            result[file.relative_to(path).as_posix()] = digest(file)
    if not result:
        raise ValueError("empty qualification input: " + str(path))
    return result


def read_json(path, limit):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("qualification record exceeds bounds")
    return json.loads(data, object_pairs_hook=unique_object)


def releases(sdk):
    index = read_json(sdk / INDEX, 4 * 1024 * 1024)
    if (not isinstance(index, dict) or index.get("format") != "wros-memory-neighbor-releases" or index.get("managed_gap_bytes") != 64
            or not isinstance(index.get("routes"), list) or len(index["routes"]) > 4096):
        raise ValueError("invalid managed-neighbor release index")
    rows = [*index["routes"], *local_release.releases(sdk)]
    for row in rows:
        if not isinstance(row, dict) or row.get("language") not in LANGUAGES:
            raise ValueError("invalid language in managed-neighbor release")
    return rows


def complete_release(row):
    """Check the same required input identities at build, link and deployment."""
    language = row["language"]
    profile = validate_profile(row.get("profile"))
    settings = row.get("settings")
    if (profile["mte"] is not True or not isinstance(settings, dict)
            or set(settings) != {"optimization", "debug"}
            or settings["optimization"] not in tuple("0123sz") or type(settings["debug"]) is not bool):
        return False
    keys = {"compiler", "sysroot", "linker", "archiver", "sdk"}
    inputs = row.get("inputs")
    return (isinstance(inputs, dict) and set(inputs) == keys
            and all(isinstance(value, str) and HEX.fullmatch(value) for value in inputs.values())
            and valid_proofs(row, profile["threads"], profile["exceptions"] == "eh"))


def valid_proofs(row, threads, eh=False):
    needed = PROOFS | ({"threads-tls"} if threads else set()) | ({"exception-unwind"} if eh else set())
    proofs = row.get("evidence")
    return (isinstance(proofs, dict) and set(proofs) == needed
            and all(isinstance(v, str) and HEX.fullmatch(v) for v in proofs.values())
            and isinstance(row.get("vm_sha256"), str) and HEX.fullmatch(row["vm_sha256"]))


def measure_inputs(language, options, profile, sdk=ROOT):
    tc = options.toolchain.resolve(strict=True)
    _, closure = make_command(tc, options.sysroots, profile, language, ["-c"], verify=True,
                              herbceptions=True if language == "cpp" else None)
    return {
        "compiler": closure["compiler_sha256"], "sysroot": closure["closure_sha256"],
        "linker": digest(tc / "bin/wasm-ld"), "archiver": digest(tc / "bin/llvm-ar"),
        "sdk": canonical({path: files(sdk / path) for path in (*COMMON, *SDK_INPUTS[language])}),
    }


def select_site_release(rows, language, digest=None):
    """Select exactly one externally verified row for the main language."""
    matches = [row for row in rows if isinstance(row, dict) and row.get("language") == language
               and complete_release(row) and (digest is None or canonical(row) == digest)]
    if len(matches) != 1:
        raise ValueError("site profile must select one signed release for " + language)
    return matches[0]


def check_site(data, sdk, language):
    from guest_profile import Profile
    site = local_release.parse_site(data)
    rows = local_release.verified_releases(site["trust"])
    row = select_site_release(rows, language, site.get("release_sha256"))
    options = argparse.Namespace(toolchain=Path(site["toolchain"]), sysroots=list(map(Path, site["sysroots"])))
    profile = Profile(**{key: row["profile"][key] for key in Profile.__dataclass_fields__})
    if measure_inputs(language, options, profile, sdk) != row["inputs"]:
        raise ValueError("site inputs differ from the signed release for this SDK")
    return canonical(row)


def frontend_profile(options, language, sdk=ROOT):
    """Resolve explicit options and the exact signed defaults used by installed drivers."""
    from guest_profile import Profile
    site = local_release.site_config(sdk)
    selected = None
    bundled = False
    defaults = dict(target="wasm32", core="3.0", threads=False, O="3", g=True)
    if (options.toolchain is None) != (options.sysroots is None):
        raise ValueError("select --toolchain and --sysroots together")
    if options.require_qualified and not options.mte:
        raise ValueError("--require-qualified requires WasmMTE")
    if site is not None and options.toolchain is None:
        if not options.mte:
            raise ValueError("the configured site release requires WasmMTE")
        row = select_site_release(local_release.verified_releases(site["trust"]), language, site.get("release_sha256"))
        selected = canonical(row)
        options.toolchain = Path(site["toolchain"])
        options.sysroots = list(map(Path, site["sysroots"]))
    elif options.toolchain is None:
        import portable_cc
        if not portable_cc.available(sdk):
            raise ValueError("install a bundled toolchain or select --toolchain and --sysroots")
        bundled = True
        index = read_json(sdk / INDEX, 4 * 1024 * 1024)
        pinned = index.get("defaults", {}).get(language)
        if pinned is not None and options.mte:
            row = select_site_release(index["routes"], language, pinned)
            selected = canonical(row)
    if selected is not None:
        preset = row["profile"]
        defaults.update(target="wasm" + str(preset["address_bits"]),
                        core="mvp" if preset["wasm_version"] == "1.0" else preset["wasm_version"],
                        eh=preset["exceptions"] == "eh", threads=preset["threads"],
                        O=row["settings"]["optimization"], g=row["settings"]["debug"])
    for key, value in defaults.items():
        if getattr(options, key) is None:
            setattr(options, key, value)
    core = "1.0" if options.core == "mvp" else options.core
    if options.eh is None:
        options.eh = core == "3.0"
    profile = Profile(int(options.target[4:]), core, options.threads, options.mte, "eh" if options.eh else "noeh")
    if bundled:
        options.toolchain, receipt = portable_cc.prepare(sdk, language=language, profile=profile)
        options.sysroots = [receipt]
    if options.toolchain is None or not options.sysroots:
        raise ValueError("--toolchain and --sysroots are required without an installed site profile")
    return profile, selected


def admit(language, options, profile, sdk=ROOT, selected_release=None):
    settings = {"optimization": options.O, "debug": options.g}
    record = {"format": "wros-build-receipt", "language": language, "profile": profile.to_dict(),
              "settings": settings, "mode": "instrumented" if profile.mte else "off",
              "source_suppressions": {"status": "not-enumerated"}, "vm_qualified": False}
    if not options.require_qualified and selected_release is None:
        return record
    rows = [row for row in releases(sdk) if row.get("language") == language
            and row.get("profile") == profile.to_dict() and row.get("settings") == settings
            and complete_release(row) and (selected_release is None or canonical(row) == selected_release)]
    if not rows:
        raise ValueError("no reviewed strict-neighbor release for " + language + "/" + profile.identity)
    inputs = measure_inputs(language, options, profile, sdk)
    matches = [row for row in rows if row["inputs"] == inputs]
    if len(matches) != 1:
        raise ValueError("no unique strict qualification matches the compiler, linker, sysroot and SDK")
    row = matches[0]
    record.update(mode="strict", scope="registered-independent-storage", vm_qualified=True,
                  release_sha256=canonical(row), vm_sha256=row["vm_sha256"])
    return record


def object_releases(admission, sdk=ROOT):
    if admission["mode"] != "strict":
        return None
    rows = releases(sdk)
    producer = next((row for row in rows if canonical(row) == admission["release_sha256"]), None)
    if producer is None:
        raise ValueError("admitted release is absent from the trusted index")
    return {canonical(row) for row in rows
            if row.get("profile") == admission["profile"] and row.get("vm_sha256") == admission["vm_sha256"]
            and complete_release(row)
            and all(row["inputs"].get(k) == producer["inputs"][k] for k in ("compiler", "linker", "sysroot"))}



def finish(record, options, staged, output, suppressions=None):
    """Bind the receipt to private bytes before publishing to a shared path.

    Concurrent publishers may replace the two files in different orders. A
    verifier detects every mismatched pair from the prepublication digest.
    """
    if not options.build_receipt:
        os.replace(staged, output)
        return
    value = dict(record, artifact_sha256=digest(staged))
    if suppressions is not None:
        value["source_suppressions"] = {"status": "frontend-reported", "definitions": suppressions}
    receipt_path = Path(str(output) + ".wros-build.json")
    # Prepare and bound the sidecar before touching a previously valid module.
    with tempfile.NamedTemporaryFile(mode="wb", dir=receipt_path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            for part in json.JSONEncoder(indent=2).iterencode(value):
                encoded = part.encode()
                if stream.tell() + len(encoded) + 1 > MAX_RECEIPT_BYTES:
                    raise ValueError("build receipt exceeds the deployment verification bound")
                stream.write(encoded)
            stream.write(b"\n")
            stream.close()
            os.replace(staged, output)
            os.replace(temporary, receipt_path)
        finally:
            temporary.unlink(missing_ok=True)


def verify(artifact, receipt, vm, approved_sha256, sdk=ROOT):
    # The caller must obtain this digest from a trusted signature or manifest.
    # Hash, parse and verify the exact same immutable receipt bytes.
    if not HEX.fullmatch(approved_sha256):
        raise ValueError("invalid trusted build receipt digest")
    with receipt.open("rb") as stream:
        data = stream.read(MAX_RECEIPT_BYTES + 1)
    if len(data) > MAX_RECEIPT_BYTES or hashlib.sha256(data).hexdigest() != approved_sha256:
        raise ValueError("build receipt differs from approved content")
    r = json.loads(data, object_pairs_hook=unique_object)
    if not isinstance(r, dict) or r.get("language") not in LANGUAGES:
        raise ValueError("invalid language build receipt")
    profile = validate_profile(r.get("profile"))
    suppressions = r.get("source_suppressions")
    if not isinstance(suppressions, dict) or not (
            suppressions == {"status": "not-enumerated"} or
            (r["language"] in {"rs", "tinygo"} and set(suppressions) == {"status", "definitions"}
             and suppressions["status"] == "frontend-reported" and isinstance(suppressions["definitions"], dict))):
        raise ValueError("invalid source suppression report")
    from frontend import audit
    from guest_profile import Profile
    content = read_bounded(artifact)
    if "shared_memory_pages" in r and (r["language"] not in {"c", "cpp", "fortran"}
                                      or type(r["shared_memory_pages"]) is not int):
        raise ValueError("invalid shared memory build contract")
    audit(content, Profile(**{key: profile[key] for key in Profile.__dataclass_fields__}),
          r.get("shared_memory_pages"), memory64=r.get("memory64"))
    if any(name in ("linking", NOTE) for _, _, name, _ in sections(content)):
        raise ValueError("deployment verification requires a linked Wasm module")
    if (profile["mte"] is not True or r.get("format") != "wros-build-receipt" or r.get("mode") != "strict"
            or r.get("scope") != "registered-independent-storage" or r.get("artifact_sha256") != hashlib.sha256(content).hexdigest()
            or r.get("vm_sha256") != digest(vm)):
        raise ValueError("build receipt does not qualify this artifact and VM")
    matches = [row for row in releases(sdk) if canonical(row) == r.get("release_sha256")
               and row["language"] == r["language"] and row["profile"] == r["profile"] and row["settings"] == r["settings"]
               and row["vm_sha256"] == r["vm_sha256"] and complete_release(row)]
    if len(matches) != 1:
        raise ValueError("build receipt refers to an unrecognized release")
    return r


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Check an approved build receipt for one artifact and deployment VM")
    for arg in ("artifact", "receipt", "vm"):
        p.add_argument("--" + arg, type=Path, required=True)
    p.add_argument("--approved-receipt-sha256", required=True)
    a = p.parse_args()
    try:
        print(json.dumps(verify(a.artifact, a.receipt, a.vm, a.approved_receipt_sha256), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.exit(1, str(error) + "\n")
