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
import shlex
import subprocess
import sys
import tempfile

from compiler import compiler_environment, digest, make_command
import local_release
from artifacts import NOTE, read_bounded, sections, unique_object, validate_profile


ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("share/qualification/memory-neighbors.json")
LANGUAGES = {"c", "cpp", "lua", "fortran", "rs", "tinygo", "nim", "objectc"}
COMMON = ("install/qualification.py", "install/local_release.py", "install/artifacts.py", "install/compiler.py", "install/guest_profile.py",
          "install/imports.py", "install/frontend.py", "install/archiver.py", "bin/wrar", "share/abi/ros.json")
SDK_INPUTS = {
    "c": ("bin/wrc", "include/wros/scene.h"),
    "cpp": ("bin/wrcc", "include/wros/scene.h"),
    "lua": ("bin/wrlua", "bin/wrcc", "include/wros/scene.h", "language/lua/entry.cpp", "language/lua/scene.hpp", "third-parties/lua"),
    "fortran": ("bin/wrfortran", "bin/wrcc", "bin/wrc", "include/wros/scene.h", "language/fortran", "third-parties/fortran"),
    "rs": ("bin/wrrust", "tools/wasm/tag_ir.cpp", "language/rust", "third-parties/rust"),
    "objectc": ("bin/wrobjc", "include/wros/scene.h", "language/objectc", "third-parties/objectc"),
    "nim": ("bin/wrnim", "bin/wrc", "language/nim", "include/wros/scene.h", "third-parties/nim/nim-2.2.4-lib.tar.xz"),
    "tinygo": ("bin/wrtinygo", "tools/wasm/tag_ir.cpp", "language/tinygo"),
}
EXTERNAL = {"objectc": {"objc_frontend", "objc_runtime", "objc_archive"}, "nim": {"producer"}, "c": set(), "cpp": set(), "lua": set(), "fortran": {"flang", "marker"},
            "rs": {"rustc", "host_cxx"}, "tinygo": {"go", "tinygo", "host_cxx"}}
PROOFS = {"compiler-stack", "global-layout", "aggregate-pointers", "heap", "language", "vm-int", "vm-aot"}
MAX_RECEIPT_BYTES = 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")


def arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mte", dest="mte", action="store_true", help="require a reviewed neighbor-aware release (default)")
    group.add_argument("--no-mte", dest="mte", action="store_false", help="build with the uninstrumented sysroot")
    group.add_argument("--legacy-mte", action="store_true", help="allow MTE without managed-neighbor qualification")
    parser.set_defaults(mte=True)
    parser.add_argument("--build-receipt", action="store_true", help="write OUTPUT.wros-build.json for artifact review")


def switch(options):
    if not options.mte:
        return "--no-mte"
    return "--legacy-mte" if options.legacy_mte else "--mte"


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
    keys = {"compiler", "sysroot", "linker", "archiver", "sdk"} | EXTERNAL[language]
    if language in ("rs", "tinygo"):
        keys |= {"llvm_config", "llvm_development"}
    if language == "fortran":
        keys.add("cpp_compiler")
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


def llvm_sdk(tc):
    cfg = tc / "bin/llvm-config"

    def flags(*args):
        return shlex.split(subprocess.check_output([cfg, *args], text=True, env=compiler_environment(tc), timeout=15))

    includes = [arg[2:] for arg in flags("--cxxflags") if arg.startswith("-I")]
    libraries = flags("--libfiles", "core", "irreader", "bitwriter")
    if not includes or not libraries or any(not Path(p).is_absolute() for p in includes + libraries):
        raise ValueError("incomplete LLVM development input inventory")
    # Identify content independently of the operator's installation prefix.
    return canonical({"include": [files(Path(p)) for p in includes],
                      "libraries": [[Path(p).name, digest(Path(p))] for p in libraries]})


def measure_inputs(language, options, profile, extra=None, sdk=ROOT, candidates=None):
    """Measure reviewed inputs, or a local developer-selected candidate before independent testing.

    A candidate with no release is accepted only by the measurement tool; the
    admission caller always supplies a nonempty trusted release selection.
    """
    if language not in LANGUAGES or not profile.mte:
        raise ValueError("expected a tagged development language profile")
    tc = options.toolchain.resolve(strict=True)
    receipts = options.sysroots if isinstance(options.sysroots, list) else [options.sysroots]
    _, closure = make_command(tc, receipts, profile, "cpp" if language in ("cpp", "lua") else "c", ["-c"], verify=True)
    inputs = {"compiler": closure["compiler_sha256"], "sysroot": closure["closure_sha256"],
              "linker": digest(tc / "bin/wasm-ld"), "archiver": digest(tc / "bin/llvm-ar")}
    extra = extra or {}
    if set(extra) != EXTERNAL[language]:
        raise ValueError("incomplete language producer identity")
    inputs.update({name: digest(Path(path)) for name, path in extra.items()})
    if language in ("rs", "tinygo"):
        inputs["llvm_config"] = digest(tc / "bin/llvm-config")
    if language == "fortran":
        inputs["cpp_compiler"] = digest(tc / "bin/clang++")
    if candidates is not None and not any(
            all(row.get("inputs", {}).get(k) == v for k, v in inputs.items()) for row in candidates):
        raise ValueError("compiler, linker, sysroot or language tools lack a reviewed strict-neighbor release")
    inputs["sdk"] = canonical({path: files(sdk / path) for path in (*COMMON, *SDK_INPUTS[language])})
    if language in ("rs", "tinygo"):
        inputs["llvm_development"] = llvm_sdk(tc)
    return inputs


def admit(language, options, profile, extra=None, sdk=ROOT):
    mode = switch(options)
    settings = {"optimization": str(getattr(options, "O", "3")),
                "debug": bool(getattr(options, "g", language in ("lua", "tinygo")))}
    record = {"settings": settings, "format": "wros-build-receipt", "language": language, "profile": profile.to_dict(),
              "mode": {"--mte": "strict", "--legacy-mte": "legacy", "--no-mte": "off"}[mode],
              "scope": "registered-independent-storage", "source_suppressions": {"status": "not-enumerated"}}
    if mode == "--legacy-mte":
        print("warning: --legacy-mte builds without managed-neighbor qualification", file=sys.stderr)
    if mode != "--mte":
        return record
    if language not in LANGUAGES or not profile.mte:
        raise ValueError("unsupported strict MTE language or target")
    candidates = [r for r in releases(sdk) if r.get("language") == language and r.get("profile") == profile.to_dict()
                  and r.get("settings") == settings]
    if not candidates:
        raise ValueError("no reviewed strict-neighbor release for " + language + "/" + profile.identity
                         + "; --legacy-mte explicitly selects unqualified MTE")
    inputs = measure_inputs(language, options, profile, extra, sdk, candidates)
    matches = [r for r in candidates if r["inputs"] == inputs and complete_release(r)]
    if len(matches) != 1:
        raise ValueError("missing or ambiguous qualification for the exact language runtime and VM")
    release = matches[0]
    record.update(release_sha256=canonical(release), vm_sha256=release["vm_sha256"])
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
    audit(content, Profile(**{key: profile[key] for key in Profile.__dataclass_fields__}))
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
