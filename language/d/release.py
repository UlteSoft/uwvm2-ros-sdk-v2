"""Measure and verify a Linux x86-64 BetterC site against an operator-signed WSEA bundle."""
import json
from pathlib import Path
import re
import subprocess
import sys

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
import local_release
import qualification
from compiler import compiler_environment, make_command, digest
from guest_profile import Profile

PROFILE = Profile(32)
SETTINGS = {"optimization": "3", "debug": True}
FORMAT = "wros-d-betterc-release-v1"
BUILD = "wros-d-betterc-build-v1"
LOADER = Path("/lib64/ld-linux-x86-64.so.2")
ENV = {"PATH": "/nonexistent", "LC_ALL": "C"}
SOURCES = (*qualification.COMMON, "bin/wrd", "include/wros/scene.h", "language/d")
PROOFS = {"frontend", "instrument", "compile", "link", "vm-int", "vm-aot", "bindings"}
canon = qualification.canonical


def dependencies(program, env):
    # GNU ld.so --list resolves the executable's startup dependencies without invoking its entry point.
    # Use the same clean environment and absolute executable for observation and compilation.
    listing = subprocess.run([LOADER, "--list", program], env=env, capture_output=True, text=True, check=True,
                             timeout=15).stdout.splitlines()
    libraries = {}
    for line in listing:
        line = line.strip()
        if line.startswith("linux-vdso.so."):
            continue
        match = re.fullmatch(r"(?:([^ /]+) => )?(/[^\n]+?) \(0x[0-9a-fA-F]+\)", line)
        if not match:
            raise ValueError("unrecognized ELF dependency in host tool closure")
        path = Path(match[2]).resolve(strict=True)
        name = match[1] or path.name
        if name in libraries or len(libraries) >= 128:
            raise ValueError("ambiguous or oversized ELF dependency list")
        libraries[name] = {"path": str(path), "sha256": digest(path)}
    if not libraries:
        raise ValueError("missing host tool ELF dependencies")
    return libraries


def host_files(toolchain, expected=None):
    if Path("/etc/ld.so.preload").exists() and Path("/etc/ld.so.preload").read_text().strip():
        raise ValueError("the qualified Linux D site requires a clean system preload configuration")
    ldc = (toolchain / "bin/wros-ldc2").resolve(strict=True)
    marker = (toolchain / "bin/wros-flang-mte").resolve(strict=True)
    marker_receipt = marker.with_name(marker.name + ".json")
    host = {"ldc": digest(ldc), "loader": digest(LOADER), "marker": digest(marker),
            "marker_receipt": digest(marker_receipt)}
    if expected is not None and any(expected.get(k) != value for k, value in host.items()):
        raise ValueError("D frontend, ELF loader or LLVM marker differs from its signed identity")
    record = json.loads(local_release.read_file(marker_receipt, 2048))
    if (record.get("format") != "wros-flang-mte" or record.get("marker_sha256") != host["marker"]
            or record.get("codegen_sha256") != digest(toolchain / "bin/clang")
            or not qualification.HEX.fullmatch(record.get("source_sha256", ""))):
        raise ValueError("the marker was built for a different LLVM code generator")

    libraries = dependencies(ldc, ENV)
    marker_libraries = dependencies(marker, compiler_environment(toolchain))
    imports = (toolchain / "share/wros/betterc/imports").resolve(strict=True)
    if not (imports / "object.d").is_file():
        raise ValueError("the site needs the matching D compiler imports, including object.d")
    host.update(libraries=libraries, marker_libraries=marker_libraries, imports=qualification.files(imports))
    return host


def measure(toolchain, sysroots, expected=None):
    host = host_files(toolchain, expected)
    _, rec = make_command(toolchain, sysroots, PROFILE, "c", ["-c"], verify=True)
    backend = {"compiler": rec["compiler_sha256"], "sysroot": rec["closure_sha256"],
               "linker": digest(toolchain / "bin/wasm-ld"), "archiver": digest(toolchain / "bin/llvm-ar")}
    inputs = {"host": host, "backend": backend,
              "sdk": canon({path: qualification.files(SDK / path) for path in SOURCES})}
    return inputs


def c_release(rows, sha, measured):
    matches = [r for r in rows if isinstance(r, dict) and r.get("language") == "c" and canon(r) == sha]
    if len(matches) != 1:
        raise ValueError("the signed bundle needs the exact reviewed C backend release")
    row = matches[0]
    if (row["profile"] != PROFILE.to_dict() or row["settings"] != SETTINGS or not qualification.complete_release(row)
            or any(row["inputs"].get(key) != value for key, value in measured.items())):
        raise ValueError("the C release does not match the BetterC code generator, linker and sysroot")
    return row


def authorized(site):
    if not site:
        raise ValueError("wrd requires an operator-signed BetterC site installation")
    rows = local_release.verified_releases(site["trust"])
    approvals = [r for r in rows if isinstance(r, dict) and r.get("format") == FORMAT and r.get("language") == "d"
                 and (site.get("release_sha256") is None or canon(r) == site["release_sha256"])]
    if len(approvals) != 1:
        raise ValueError("the site needs exactly one approved D BetterC release")
    row = approvals[0]
    if (row.get("profile") != PROFILE.to_dict() or row.get("settings") != SETTINGS
            or not isinstance(row.get("evidence"), dict) or set(row["evidence"]) != PROOFS
            or not all(isinstance(v, str) and qualification.HEX.fullmatch(v) for v in row["evidence"].values())):
        raise ValueError("incomplete D language or VM qualification")
    if not isinstance(row.get("inputs"), dict) or not isinstance(row["inputs"].get("host"), dict):
        raise ValueError("missing signed D host inventory")
    tc = Path(site["toolchain"]).resolve(strict=True)
    manifests = list(map(Path, site["sysroots"]))
    measured = measure(tc, manifests, row["inputs"]["host"])
    parent = c_release(rows, row["c_release_sha256"], measured["backend"])
    if row["inputs"] != measured or row.get("vm_sha256") != parent["vm_sha256"]:
        raise ValueError("the installed D frontend, host libraries, D imports, SDK or VM differ from the signed row")
    return row
