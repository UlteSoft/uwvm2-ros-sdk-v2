"""Exercise package:// lookup against acquired, content-addressed ROS sources in both VM engines."""
import argparse
import collections
import contextlib
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from urllib.parse import quote

SDK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SDK / "tools/migration"), str(SDK / "install")]
from audit_ros_packages import digest, json_lines, source_manifest
from package_resources import collect, write_pack
from guest_profile import Profile
from imports import inspect

ASSETS = (("msg", ".msg"), ("srv", ".srv"), ("action", ".action"), ("urdf", ".urdf"),
          ("urdf", ".xacro"), ("srdf", ".srdf"), ("config", ".yaml"), ("launch", ".launch"))
MAX_ASSET_BYTES = 16384


@contextlib.contextmanager
def exclusive(path):
    with path.open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def selected_asset(root):
    """Select at most one small, regular, direct-child source asset per original package."""
    for directory, suffix in ASSETS:
        folder = root / directory
        if folder.is_symlink() or not folder.is_dir():
            continue
        for path in sorted(folder.glob("*" + suffix)):
            if not path.is_symlink() and path.is_file() and path.stat().st_size <= MAX_ASSET_BYTES:
                return path
    return None


def golden(path, limit):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("source exceeded the size limit")
    return data


def review(args):
    cases = {}
    stats = collections.Counter()
    names = set()
    with gzip.open(args.manifests, "rt") as reports, json_lines(args.output / "variants.jsonl.gz") as log:
        for line in reports:
            variant = json.loads(line)
            record = {k: variant[k] for k in ("package", "source_id", "manifest", "archive_sha256", "state")}
            if variant["state"] == "manifest-read":
                try:
                    manifest = source_manifest(args.corpus, record["source_id"], record["manifest"])
                    root = manifest.parent
                    asset = selected_asset(root)
                    paths = [manifest] if asset is None else [manifest, asset]
                    expected = {}
                    for path in paths:
                        uri = "package://" + record["package"] + "/" + quote(path.relative_to(root).as_posix())
                        expected[uri] = golden(path, 1048576 if path == manifest else MAX_ASSET_BYTES)
                    if hashlib.sha256(next(iter(expected.values()))).hexdigest() != variant["manifest_sha256"]:
                        raise ValueError("source manifest changed after the audit")
                    rows = collect([root], list(expected), False)
                    if any(data != expected[entry["uri"]] for entry, data in rows):
                        raise ValueError("packed bytes differ from an independent source read")
                    keys = [entry for entry, data in rows]
                    case = hashlib.sha256(json.dumps(keys, sort_keys=True).encode()).hexdigest()
                    if case not in cases:
                        cases[case] = (rows, [(uri, data) for uri, data in sorted(expected.items())])
                    record.update(state="resource-selected", case=case, entries=keys)
                    names.add(record["package"])
                except (OSError, ValueError) as exc:
                    record.update(state="resource-review-required", reason=str(exc))
            else:
                record["reason"] = variant.get("reason")
            stats[record["state"]] += 1
            log.write(json.dumps(record, separators=(",", ":")) + "\n")
    return cases, dict(stats), len(names)


def batches(cases):
    # Distinct source versions can publish different bytes at the same package URI.
    # Each pack is a single unambiguous namespace. Never drop a conflicting version.
    groups = []
    for case, (rows, _) in sorted(cases.items()):
        keys = {entry["uri"] for entry, _ in rows}
        cost = sum(16 + len(entry["uri"]) + len(data) for entry, data in rows)
        for seen, ids, budget in groups:
            if not seen.intersection(keys) and budget[0] + cost <= 2 * 1024 * 1024:
                break
        else:
            seen, ids, budget = set(), [], [16]
            groups.append((seen, ids, budget))
        seen.update(keys)
        ids.append(case)
        budget[0] += cost
    return [ids for _, ids, _ in groups]


def expectations(file, items):
    for uri, data in items:
        code = 14695981039346656037
        for byte in data:
            code = ((code ^ byte) * 1099511628211) & 0xffffffffffffffff
        key = uri.encode("ascii")
        file.write(struct.pack("<IIQ", len(key), len(data), code))
        file.write(key)


def run_one(folder, report, label, cmd):
    args = list(map(str, cmd))
    with (folder / "command.log").open("wb") as log:
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=360, cwd=folder)
    report[label] = {"argv": args, "exit": result.returncode}
    if result.returncode:
        report[label]["diagnostic"] = (folder / "command.log").read_bytes()[-8192:].decode(errors="replace")
        raise ValueError(label + " failed")


def qualify(args, ids, cases, folder, report):
    rows = sorted((row for case in ids for row in cases[case][0]), key=lambda row: row[0]["uri"])
    with (folder / "resources.bin").open("wb") as pack:
        write_pack(pack, rows)
    with (folder / "expected.bin").open("wb") as expected:
        expectations(expected, sorted(row for case in ids for row in cases[case][1]))
    guest = folder / "package_resource_guest.c"
    shutil.copyfile(Path(__file__).with_name(guest.name), guest)
    flags = ["-O3", "-g", "-I" + str(args.include), guest]
    report.update(entries=len(rows), pack_sha256=digest(folder / "resources.bin"),
                  expectations_sha256=digest(folder / "expected.bin"))
    run_one(folder, report, "native_build", [args.clang, "-std=c23", *flags, "-o", folder / "native"])
    run_one(folder, report, "native", [folder / "native"])
    for bits in (32, 64):
        wasm = folder / f"resource{bits}.wasm"
        profile = Profile(bits)
        mode = ["--legacy-mte"] if args.candidate_mte else []
        run_one(folder, report, f"wasm{bits}_build", [args.wrc, "--std", "c23", "--toolchain", args.toolchain,
                "--sysroots", getattr(args, f"sysroots{bits}"), "--target", f"wasm{bits}", *mode, "--reactor",
                "--export", "_start", *flags, "-o", wasm])
        if inspect(wasm.read_bytes()):
            raise ValueError("guest contains host imports")
        report[f"wasm{bits}_sha256"] = digest(wasm)
        for engine in ("int", "aot"):
            run_one(folder, report, f"wasm{bits}_{engine}", [args.runtime, *profile.uwvm_feature_flags(),
                    "--runtime-" + engine, "--runtime-memtag-mode", "sync", "--runtime-memtag-backend", "software",
                    "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                    "--debug-fault-action", "exit", "--run", wasm])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for k in ("corpus", "manifests", "output", "wrc", "include", "clang", "toolchain", "sysroots32",
              "sysroots64", "runtime", "lock"):
        parser.add_argument("--" + k, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--candidate-mte", action="store_true", help="Use the explicit development producer.")
    args = parser.parse_args()
    group = Path("/proc/self/cgroup").read_text().strip()
    path = Path("/sys/fs/cgroup") / group.removeprefix("0::/") if group.startswith("0::/") else None
    if path is None or (path / "memory.max").read_text().strip() != "68719476736" or (path / "memory.swap.max").read_text().strip() != "0":
        raise SystemExit("requires the 64 GiB cgroup with zero swap")
    args.output.mkdir(parents=True, exist_ok=False)
    with exclusive(args.lock):
        cases, states, names = review(args)
        groups = batches(cases)
        receipt = dict(cgroup=group, complete=False, candidate_mte=args.candidate_mte,
                       states=states, packages_selected=names, unique_source_vectors=len(cases), batches=len(groups),
                       runtime_sha256=digest(args.runtime), wrc_sha256=digest(args.wrc),
                       manifests_sha256=digest(args.manifests), reader_sha256=digest(args.include / "wros/package_resources.h"),
                       guest_sha256=digest(Path(__file__).with_name("package_resource_guest.c")),
                       scope="Exact package URI and asset byte lookup only. Whole-package and driver qualification are separate.")
    result = args.output / "results.json"
    result.write_text(json.dumps(receipt, indent=2) + "\n")
    passed = 0
    for ordinal, ids in enumerate(groups):
        report = dict(ordinal=ordinal, case_ids=ids, passed=False)
        with exclusive(args.lock), tempfile.TemporaryDirectory(dir=args.output) as tmp:
            try:
                qualify(args, ids, cases, Path(tmp), report)
                report["passed"] = True
            except (OSError, ValueError, subprocess.TimeoutExpired) as err:
                report["error"] = str(err)
            (args.output / f"batch-{ordinal:04d}.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"batch {ordinal+1}/{len(groups)}: {report['passed']}", flush=True)
        if not report["passed"]:
            break
        passed += 1
    receipt.update(passed_batches=passed, complete=bool(groups) and passed == len(groups))
    result.write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
