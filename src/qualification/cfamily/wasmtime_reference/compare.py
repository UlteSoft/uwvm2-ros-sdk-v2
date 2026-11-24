#!/usr/bin/env python3
"""Compare non-MTE C/C++ qualification guests with the Wasmtime C API adapter."""
import argparse
import itertools
import json
import platform
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent
sys.path.insert(0, str(SUITE))
from sysroot_suite import SHARED_MEMORY_PAGES, Target, add_vm_identity_options, digest, validate_thread_budgets
from wasmtime_reference.adapter import (WASMTIME_COMMIT, checked_hash, compare_engines, recorded_policy,
                                        require, run_host, saved_engines)

REFERENCE = "Wasmtime 42.0.1 C API with the external C-family qualification adapter"


def execute(args, row, target, case, out, original):
    require(row["status"] == "linked", "SDK did not link this case")
    counts = row["opcodes"]
    require(counts["memtag_total"] == 0 and counts["thread_spawn_imports"] == 0
            and counts["shared_memories"] == int(target.threads), "unsupported guest features")
    guest = original / "guest.wasm"
    checked_hash(guest, row["wasm_sha256"])
    checked_hash(SUITE / case["path"], row["source_sha256"])
    owner = None
    owner_hash = None
    if target.threads:
        memory, = [item for item in row["imports"] if item["kind"] == 2]
        flags, minimum, maximum = memory["limits"]
        require((memory["module"], memory["name"]) == ("env", "memory")
                and flags == (7 if target.bits == 64 else 3)
                and 0 < minimum <= maximum == SHARED_MEMORY_PAGES, "unexpected owner memory limits")
        owner = original / "owner.wasm"
        owner_hash = checked_hash(owner, row["memory_owner"]["sha256"])

    return {**run_host(args, target, guest, owner, recorded_policy(row, target, case), out), "owner_sha256": owner_hash}


def compare_case(args, row, target, case):
    result = {key: row[key] for key in ("profile", "family", "source", "wasm_sha256") if key in row}
    result["reference"] = REFERENCE
    source = Path(case["path"])
    relative = Path(target.name) / case["family"] / source.parent.name / source.name
    original, out = args.results / relative, args.work / relative
    try:
        require(case["family"] == row["family"], "recorded case family disagrees with manifest")
        out.mkdir(parents=True)
        result.update(execute(args, row, target, case, out, original))
        result["engines"] = compare_engines(saved_engines(row, original), result)
        if "expected_stdout" in case:
            answer = SUITE / "upstream" / case["family"] / case["expected_stdout"]
            result["upstream_stdout_sha256"] = digest(answer)
            result["upstream_stdout_equal"] = result["stdout_sha256"] == result["upstream_stdout_sha256"]
    except (IndexError, KeyError, OSError, TypeError, ValueError) as exc:
        result["harness_error"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("host", "results", "work"):
        parser.add_argument("--" + name, type=lambda s: Path(s).resolve(), required=True)
    parser.add_argument("--suite", choices=("external", "sysroot"), default="external")
    parser.add_argument("--decoder", type=Path, help="native qualification decoder for sysroot replay")
    parser.add_argument("--compiler-sources", type=Path,
                        help="matching src/compilers/cc containing the Open POSIX inputs and policy/imports.py")
    parser.add_argument("--qualification-receipt", type=Path, help="production sysroot-receipt.json")
    parser.add_argument("--host-sha256", help="verify the adapter executable against a trusted build digest")
    parser.add_argument("--vm", type=Path, help="original VM executable for checking the producer identity")
    add_vm_identity_options(parser)
    parser.set_defaults(vm_target=None)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.work == args.results or args.results in args.work.parents:
        parser.error("use a separate adapter output directory")
    if args.jobs < 1 or args.timeout < 1:
        parser.error("jobs and timeout must be positive")
    if args.suite == "sysroot" and args.decoder is None:
        parser.error("--suite sysroot requires --decoder")
    if args.suite == "external" and any((args.decoder, args.compiler_sources, args.qualification_receipt, args.vm)):
        parser.error("--decoder, --compiler-sources, --qualification-receipt and --vm apply to --suite sysroot")
    if (args.vm_receipt or args.vm_target) and not args.vm:
        parser.error("--vm-target and --vm-receipt require --vm")
    if args.vm and args.vm_target is None:
        args.vm_target = SUITE.parents[2] / "document/qualification/runtime-qualification.json"
    args.work.mkdir(parents=True, exist_ok=True)
    if any(args.work.iterdir()):
        parser.error("choose an empty adapter output directory to preserve evidence")
    if args.suite == "sysroot":
        from wasmtime_reference.sysroot import EVIDENCE_ERRORS, compare_sysroot, write_json
        args.compiler_sources = args.compiler_sources or SUITE.parents[1] / "compilers/cc"
        try:
            return compare_sysroot(args)
        except EVIDENCE_ERRORS as exc:
            error = {"suite": "sysroot", "complete": False, "passed": False, "exit_code": 1,
                     "status": "evidence-error", "reason": str(exc)}
            write_json(args.work / "summary.json", error)
            print(json.dumps(error), file=sys.stderr)
            return 1

    if args.host_sha256:
        checked_hash(args.host, args.host_sha256)
    manifest_file = SUITE / "external-libraries.json"
    manifest = json.loads(manifest_file.read_bytes())
    validate_thread_budgets(manifest["cases"])
    cases = {case["path"]: case for case in manifest["cases"]}
    profiles = {t.name: t for t in (Target(bits, threads, False, eh) for bits, threads, eh in
                itertools.product((32, 64), (False, True), (False, True)))}
    inputs_file = args.results / "inputs.json"
    inputs = json.loads(inputs_file.read_bytes())
    checked_hash(manifest_file, inputs["manifest_sha256"])
    records = args.results / "results.jsonl"
    rows = [row for line in records.read_text().splitlines() if (row := json.loads(line))["profile"].endswith("-nomte")]
    keys = [(row["profile"], row["source"]) for row in rows]
    expected = set(itertools.product(profiles, cases))
    require(len(keys) == len(expected) and set(keys) == expected, "incomplete or duplicate non-MTE case/profile matrix")
    meta = {"reference": REFERENCE, "machine": platform.machine(),
            "wasmtime_release_commit": WASMTIME_COMMIT,
            "host_binary_sha256": digest(args.host), "host_source_sha256": digest(HERE / "host.cpp"),
            "driver_sha256": digest(Path(__file__)), "adapter_driver_sha256": digest(HERE / "adapter.py"),
            "suite_policy_sha256": digest(SUITE / "sysroot_suite.py"),
            "original_results_sha256": digest(records), "original_inputs_sha256": digest(inputs_file),
            "original_runner_sha256": inputs["runner_sha256"], "manifest_sha256": inputs["manifest_sha256"],
            "planned_cases": len(rows), "guest_environment": [], "guest_preopens": [],
            "guest_args_imported": False, "stdin": "EOF with fd_read denied"}
    (args.work / "inputs.json").write_text(json.dumps(meta, indent=2) + "\n")
    terminations = Counter()
    engine_counts = {engine: Counter() for engine in ("int", "aot")}
    successful = True
    with (args.work / "results.jsonl").open("x") as log, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(lambda r: compare_case(args, r, profiles[r["profile"]], cases[r["source"]]), rows):
            print(json.dumps(row, sort_keys=True), file=log, flush=True)
            terminations["harness-error" if "harness_error" in row else row["termination"]] += 1
            successful &= ("harness_error" not in row and row.get("guest_exit_code") == 0
                           and row.get("upstream_stdout_equal", True))
            for engine in engine_counts:
                verdict = row.get("engines", {}).get(engine, {}).get("comparison", "unavailable")
                engine_counts[engine][verdict] += 1
                successful &= verdict == "match"
    summary = {**meta, "terminations": terminations, "comparisons": engine_counts}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return 0 if successful else 1


if __name__ == "__main__":
    sys.exit(main())
