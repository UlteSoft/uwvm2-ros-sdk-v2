#!/usr/bin/env python3
"""Execute the non-MTE external C-family corpus under the Wasmtime qualification adapter."""
import argparse
import itertools
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent
sys.path.insert(0, str(SUITE))
from sysroot_suite import SHARED_MEMORY_PAGES, Target, digest, runtime_args

REFERENCE = "Wasmtime 42.0.1 C API with the external C-family qualification adapter"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_hash(path, expected):
    actual = digest(path)
    require(actual == expected, f"SHA-256 mismatch for {path}")
    return actual


def recorded_policy(row, target, case):
    owner = row["memory_owner"]["argv"][-1] if target.threads else None
    guest = row["compile"]["argv"][-1]
    for engine in ("int", "aot"):
        recorded = row["runs"][engine]["argv"]
        expected = runtime_args(recorded[0], engine, target, row["imports"], owner, guest,
                                thread_stack_mib=case.get("thread_stack_mib", 1),
                                thread_storage_mib=case.get("thread_storage_mib", 16))
        require(recorded == expected, f"recorded {engine} arguments differ from the suite profile")
    options = []
    for i, flag in enumerate(recorded):
        if flag == "--wasip1-single-interface":
            options.append(f"{recorded[i + 3]}={recorded[i + 2]}")
        elif flag == "--wasip1-single-grant":
            options.append("grant=" + recorded[i + 2])
    return options


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

    report = out / "host.log"
    argv = [str(args.host), str(target.bits), "eh" if target.eh else "noeh",
            str(guest), str(owner) if owner else "-", str(report), *recorded_policy(row, target, case)]
    result = {"argv": argv, "owner_sha256": owner_hash}
    with (out / "stdout").open("xb") as stdout, (out / "stderr").open("xb") as stderr:
        try:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                  timeout=args.timeout)
            result["host_returncode"] = proc.returncode
        except subprocess.TimeoutExpired:
            result["timeout_seconds"] = args.timeout
    lines = report.read_text(errors="replace").splitlines() if report.exists() else []
    result["stdout_sha256"] = digest(out / "stdout")
    result["stderr_sha256"] = digest(out / "stderr")
    result["host_log_sha256"] = digest(report) if report.exists() else None
    result["start_invoked"] = "invoke _start" in lines
    end = re.fullmatch(r"end (returned|proc_exit) ([0-9]+)", lines[-1]) if lines else None
    if result.get("host_returncode") == 0 and result["start_invoked"] and end:
        result["termination"], result["guest_exit_code"] = end.group(1), int(end.group(2))
    elif "timeout_seconds" in result:
        result["termination"] = "timeout"
    else:
        result["termination"] = "execution-error" if result["start_invoked"] else "setup-or-instantiation-error"
    return result


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
        guest_code = result.get("guest_exit_code")
        comparisons = {}
        for engine in ("int", "aot"):
            saved = row["runs"][engine]
            stdout_hash = digest(original / (engine + ".out"))
            stderr_hash = digest(original / (engine + ".err"))
            fields = {"returncode": saved.get("returncode"), "saved_suite_status": saved["status"],
                      "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash}
            if guest_code is None or fields["returncode"] is None:
                fields["comparison"] = "unavailable"
            else:
                fields["exit_equal"] = fields["returncode"] == guest_code
                fields["stdout_equal"] = stdout_hash == result["stdout_sha256"]
                fields["stderr_equal"] = stderr_hash == result["stderr_sha256"]
                agrees = fields["exit_equal"] and fields["stdout_equal"] and fields["stderr_equal"]
                fields["comparison"] = "match" if agrees else "difference"
            comparisons[engine] = fields
        result["engines"] = comparisons
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
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.work == args.results or args.results in args.work.parents:
        parser.error("use a separate adapter output directory")
    if args.jobs < 1 or args.timeout < 1:
        parser.error("jobs and timeout must be positive")
    args.work.mkdir(parents=True, exist_ok=True)
    if any(args.work.iterdir()):
        parser.error("choose an empty adapter output directory to preserve evidence")
    manifest_file = SUITE / "external-libraries.json"
    manifest = json.loads(manifest_file.read_bytes())
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
            "wasmtime_release_commit": "6844a83b530f86ad13a65175282fe2dbcd33cad1",
            "host_binary_sha256": digest(args.host), "host_source_sha256": digest(HERE / "host.cpp"),
            "driver_sha256": digest(Path(__file__)), "suite_policy_sha256": digest(SUITE / "sysroot_suite.py"),
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
