"""Compile the same numerical probe for native and strict, import-free Wasm."""
import argparse
import hashlib
import json
import os
import resource
from pathlib import Path, PurePosixPath
import subprocess
import sys

from upstream_cpp import INCLUDE, Profile, SourceArchive, cgroup_record, inspect, put, save, sha


def run(folder, name, argv, expect=0):
    command = list(map(str, argv))
    with (folder / (name + ".log")).open("xb") as log:
        result = subprocess.run(command, cwd=folder, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if expect is None:
        if result.returncode == 0:
            raise ValueError(f"{name} accepted the altered reference")
    elif result.returncode != expect:
        raise ValueError(f"{name} exited {result.returncode}, see {folder}/{name}.log")
    return result.returncode


def compare(folder, sources, sdk, vm, native, denied_imports):
    """Require success and an observed guest trap for the changed-reference control."""
    recorded = {}
    for negative in (False, True):
        label = "changed-reference" if negative else "reference"
        (folder / "expected.h").write_text(f"#define ALTER_EXPECTATION {int(negative)}\n")
        guest = folder / (label + ".wasm")
        oracle = folder / ("native-" + label)
        run(folder, label + "-compile-native", [native, "-std=c++20", "-O3", "-g", "-Wall", "-Wextra",
                                               "-I", folder / "include", *sources, "-o", oracle])
        code = run(folder, label + "-native", [oracle], 17 if negative else 0)
        run(folder, label + "-wrcc", [sdk / "bin/wrcc", "--target", "wasm32", "--std", "c++20",
            "-O3", "-g", "--reactor", "--export", "_start", "-I", folder / "include",
            "--build-receipt", *sources, "-o", guest])
        receipt = Path(str(guest) + ".wros-build.json")
        info = json.loads(receipt.read_bytes())
        if info["mode"] != "strict":
            raise ValueError("expected a strictly qualified build")
        imports = inspect(guest.read_bytes())
        policy = []
        if imports:
            policy = ["--wasm-set-main-module-name", "numeric_guest", "--wasip1-single-create", "numeric_guest",
                      "--wasip1-single-enable", "numeric_guest"]
            for item in imports:
                if (item["module"] != "wasi_snapshot_preview1" or item["kind"] != 0 or
                        denied_imports.get(item["name"]) != (item.get("params"), item.get("results"))):
                    raise ValueError(f"unexpected host import {item!r}")
                policy.extend(["--wasip1-single-interface", "numeric_guest", item["name"], "deny"])
        run(folder, label + "-verify", [sys.executable, "-B", sdk / "install/qualification.py",
            "--vm", vm, "--artifact", guest, "--receipt", receipt, "--approved-receipt-sha256", sha(receipt)])
        engines = {}
        for engine in ("int", "aot"):
            name = label + "-" + engine
            rc = run(folder, name, [vm, *Profile().uwvm_feature_flags(), "--debug-fault-action", "exit",
                       "--runtime-" + engine, "--runtime-compile-threads", "0",
                       "--runtime-llvm-jit-cache-path", "disable", *policy, "--run", guest], None if negative else 0)
            if negative and "unreachable" not in (folder / (name + ".log")).read_text(errors="replace").lower():
                raise ValueError(f"{name} failed without the expected guest trap")
            engines[engine] = rc
        recorded[label] = dict(nativeExit=code, vmExits=engines, hostImports=imports, vmPolicy=policy, wasmSha256=sha(guest),
                               strictBuildReceiptSha256=sha(receipt))
    return recorded


def qualify(package, scope, runner, entries, absent, vectors, adapter, dependencies=None, denied_imports=None):
    fixture = runner.with_suffix(".cpp")
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("corpus", "sdk", "vm", "output"):
        p.add_argument("--" + key, type=lambda s: Path(s).resolve(), required=True)
    p.add_argument("--native-cxx", type=lambda s: Path(s).resolve(), default=Path("/usr/bin/g++"))
    args = p.parse_args()
    group = cgroup_record()
    if ".tmp" not in args.output.parts:
        p.error("choose a fresh output directory under .tmp")
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(args.output)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    inventory = args.corpus / "linux-five-capability-inventory/packages.json"
    packages = {r["name"]: r for r in json.loads(inventory.read_bytes())}
    row = packages[package]
    header, frames = vectors()
    result = dict(complete=False, package=package, scope=scope,
                  frames=frames, inventorySha256=sha(inventory), cgroup=group, vmSha256=sha(args.vm),
                  nativeCompilerSha256=sha(args.native_cxx), fixtureSha256=sha(fixture),
                  runnerSha256=sha(runner), sharedRunnerSha256=sha(Path(__file__)),
                  dependencies={}, snapshots=[], variants={})
    target = args.output / "results.json"
    save(target, result)
    for entry in row["instances"]:
        archive = SourceArchive(args.corpus, entry)
        try:
            obs = dict(sourceId=entry["source_id"], archiveSha256=entry["archive_sha256"],
                       manifest=entry["manifest"])
            result["snapshots"].append(obs)
            entrypoint = next((e for e in entries if e in archive.files), None)
            if entrypoint is None:
                obs["status"] = absent
            else:
                files = archive.closure(entrypoint)
                includes = {name for data in files.values() for name in INCLUDE.findall(data.decode(errors="surrogateescape"))}
                for include, (dependency, source_id) in (dependencies or {}).items():
                    if include not in includes:
                        continue
                    ref, = [i for i in packages[dependency]["instances"] if i["source_id"] == source_id]
                    dep_archive = SourceArchive(args.corpus, ref)
                    try:
                        dep_files = dep_archive.closure(PurePosixPath("include", include))
                        if files.keys() & dep_files.keys():
                            raise ValueError("ambiguous dependency include paths")
                        files.update(dep_files)
                        result["dependencies"][include] = dict(package=dependency, instance=ref)
                    finally:
                        dep_archive.tar.close()
                pins = {str(path): hashlib.sha256(data).hexdigest() for path, data in files.items()}
                key = hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()
                if key not in result["variants"]:
                    folder = args.output / key
                    folder.mkdir()
                    for path, data in files.items():
                        put(folder, path, data)
                    (folder / "vectors.h").write_text(header)
                    (folder / "adapter.h").write_text(adapter(files, entrypoint))
                    put(folder, "driver.cpp", fixture.read_bytes())
                    sources = [folder / p for p in files if p.suffix == ".cpp"] + [folder / "driver.cpp"]
                    cases = compare(folder, sources, args.sdk, args.vm, args.native_cxx, denied_imports or {})
                    result["variants"][key] = dict(sources=pins, runs=cases)
                obs.update(status="matched-qualified-source", variant=key)
        finally:
            archive.tar.close()
            save(target, result)
    if not result["variants"]:
        raise ValueError("no implementation was tested for " + package)
    result["complete"] = True
    save(target, result)
