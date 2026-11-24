#!/usr/bin/env python3
"""Replay the non-MTE Objective-C matrix with the reviewed Wasmtime C API host."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import cache
import itertools
import json
import os
from pathlib import Path
import platform
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import matrix
from sysroot_suite import (PERMISSIONS, SHARED_MEMORY_PAGES, Target, add_vm_identity_options, capture, digest,
                           runtime_args, verified_vm)

ENGINES = ("int", "aot")
WASMTIME_VERSION = "42.0.1"
WASMTIME_COMMIT = "6844a83b530f86ad13a65175282fe2dbcd33cad1"
EVIDENCE_ERRORS = (AttributeError, IndexError, KeyError, OSError, TypeError, ValueError)
PROFILES = {t.name: t for t in (Target(bits, threads, False, eh) for bits, threads, eh in
                                itertools.product((32, 64), (False, True), (False, True)))}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_bytes())


def checked_hash(path, expected):
    actual = digest(path)
    require(actual == expected, f"SHA-256 mismatch for {path}: expected {expected}, got {actual}")
    return actual


def diagnostic(case, target):
    if case.get("missing_header"):
        pattern = re.compile(r"fatal error: '" + re.escape(case["missing_header"]) + "' file not found")
        return "dependency-unavailable", "compile-member", pattern
    if case.get("requires_eh") and not target.eh:
        return "eh-disabled-rejected", "compile-noeh", matrix.EXCEPTION_DIAGNOSTIC
    return None


def original_tools(args, inputs):
    paths = {"u2ros": args.vm, "wrwat": args.wrwat, "C-family runner": args.matrix_policy,
             "imports reader": args.objc_sdk / "install/imports.py"}
    for language, sdk in args.sdks.items():
        driver = matrix.DRIVERS[language]
        paths[driver] = sdk / "bin" / driver
        paths[language + " llvm-ar"] = sdk / "share/toolchains/portable/bin/llvm-ar"
    results = {}
    for label, path in paths.items():
        info = results[label] = {"witness": str(path)}
        try:
            receipt = inputs["tools"][label]
            info.update(path=receipt["path"], expected_sha256=receipt["sha256"])
            info["sha256"] = checked_hash(path, receipt["sha256"])
        except EVIDENCE_ERRORS as error:
            info["error"] = str(error)
    return results


def tool_path(tools, name):
    record = tools[name]
    require("error" not in record, f"{name} witness: {record.get('error')}")
    return Path(record["path"])


@cache
def runtime_receipt(sdk, target):
    triple = f"wasm{target.bits}-wasip1" + ("-threads" if target.threads else "")
    eh = "eh" if target.eh else "noeh"
    flavor = f"core3.0-{eh}-nomte"
    path = sdk / "share/uwros/objc" / triple / flavor / "runtime.json"
    receipt = read_json(path)
    profile = {"address_bits": target.bits, "wasm_version": "3.0", "threads": target.threads, "mte": False,
               "exceptions": eh, "triple": triple, "memtag_wire": None, "extensions": ["threads"] if target.threads else [],
               "abi": "wasi_snapshot_preview1" if target.bits == 32 else "uwvm-preview1-memory64-extension"}
    require(receipt["format"] == "uwros-gnustep-guest-v2" and receipt["profile"] == profile,
            f"Objective-C runtime receipt disagrees with {target.name}")
    archives = {}
    for name in ("libobjc.a", "libuwrosobjc.a"):
        archive = Path("lib") / triple / flavor / name
        archives[name] = checked_hash(sdk / archive, receipt["files"][str(archive)])
    return {"runtime_receipt_sha256": digest(path), "runtime_archives": archives, "abi": profile["abi"]}


def stage_captures(original, row, stage):
    detail = row["stages"][stage]
    for ext, key in (("out", "stdout_sha256"), ("err", "stderr_sha256")):
        checked_hash(original / f"{stage}.{ext}", detail[key])
    return detail


def build_evidence(args, row, case, target, original, negative):
    tools = args.tools
    driver = tool_path(tools, matrix.DRIVERS[case["language"]])
    original_suite = tool_path(tools, "C-family runner").parent.parent / "objc"
    # Reconstruct the producer's paths, even when replaying on another host.
    base = matrix.tool_command(driver.parent.parent, case, target)
    base = [original_suite / p.relative_to(HERE) if isinstance(p, Path) and p.is_relative_to(HERE) else p
            for p in base]
    stage = negative[1] if negative else "link"
    recorded = row["stages"][stage]["argv"]
    directory = Path(recorded[-1]).parent
    require(directory.parts[-2:] == (target.name, case["id"]), "compiler output belongs to another cell")

    def check_stage(name, argv):
        detail = stage_captures(original, row, name)
        require(detail["argv"] == list(map(str, argv)), f"{name} argv differs from the Objective-C matrix")
        if not negative or name != stage:
            require(detail.get("returncode") == 0 and "timeout_seconds" not in detail, f"{name} did not complete")
        return detail

    if "member" in case:
        obj = directory / "member.o"
        check_stage("compile-member", [*base, "-c", original_suite / case["member"], "-o", obj])
        if stage != "compile-member":
            archive = directory / "component.a"
            check_stage("archive", [tool_path(tools, case["language"] + " llvm-ar"), "rcsD", archive, obj])
            sources = [original_suite / case["client"], archive]
    elif "units" in case:
        sources = [directory / "libobjc2" / unit for unit in case["units"]]
    else:
        sources = [original_suite / case["client"]]
    if negative:
        status, stage, pattern = negative
        if stage == "compile-noeh":
            check_stage(stage, [*base, "-c", sources[0], "-o", directory / "noeh.o"])
        rejection = row["stages"][stage]
        require(row["status"] == status and not row["runs"] and "wasm_sha256" not in row
                and not {"link", *ENGINES}.intersection(row["stages"]) and rejection.get("returncode", 0) > 0
                and matrix.build_status(original, stage, rejection, pattern, status) == status,
                f"missing expected {status} diagnostic")
    else:
        pages = ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)] if target.threads else []
        check_stage("link", [*base, *pages, *sources, "-o", directory / "guest.wasm"])
        if target.threads:
            check_stage("memory-owner", [tool_path(tools, "wrwat"), directory / "owner.wat", "--target",
                        f"wasm{target.bits}", "--core", "3.0", "--threads", "-o", directory / "owner.wasm"])
    return directory


def verify_owner(reader, data, limits):
    # Wasm import subtyping would also accept a narrower owner. The matrix uses
    # exactly the guest's min/max, exports memory 0, and has no initialization.
    module = reader.Reader(data)
    reader.require_core(module)
    seen = set()
    while module.position < len(module.data):
        section = module.byte()
        payload = reader.Reader(module.take(module.uint()))
        if section == 0:
            continue
        require(section in (5, 7) and section not in seen and payload.uint() == 1, "unexpected memory owner section")
        seen.add(section)
        if section == 5:
            require(list(payload.limits()) == limits, "owner and guest memory limits differ")
        else:
            require(payload.name() == "memory" and payload.byte() == 2 and payload.uint() == 0,
                    "owner must export memory index zero")
        payload.end()
    require(seen == {5, 7}, "incomplete memory owner")


def inspect_guest(args, row, case, target, original, out, result):
    guest = original / "guest.wasm"
    result["wasm_sha256"] = checked_hash(guest, row["wasm_sha256"])
    widths = []
    imports = args.reader.inspect(guest.read_bytes(), memory_types=widths, memory_limits=True)
    for entry in imports:
        if "limits" in entry:
            entry["limits"] = list(entry["limits"])
        if entry["module"] == "wasi_snapshot_preview1":
            require(entry["kind"] == 0 and entry["name"].endswith("_wasm64") == (target.bits == 64),
                    f"incorrect Preview1 ABI for {entry['name']}")
    require(widths == [target.bits] and imports == row["imports"], "actual memory width or imports disagree with receipt")
    result["imports"] = imports
    owner = None
    memories = [entry for entry in imports if entry["kind"] == 2]
    if target.threads:
        require(len(memories) == 1, "threaded guest must import one shared memory")
        memory, = memories
        limits = memory["limits"]
        flags, minimum, maximum = limits
        require((memory["module"], memory["name"]) == ("env", "memory") and flags == (7 if target.bits == 64 else 3)
                and 0 < minimum <= maximum == SHARED_MEMORY_PAGES, "unexpected shared memory import")
        owner = original / "owner.wasm"
        result["memory_owner_sha256"] = checked_hash(owner, row["memory_owner_sha256"])
        verify_owner(args.reader, owner.read_bytes(), limits)
        width = "i64 " if target.bits == 64 else ""
        require((original / "owner.wat").read_text() == f'(module (memory (export "memory") {width}{minimum} {maximum} shared))\n',
                "owner WAT differs from guest memory declaration")
    else:
        require(not memories and "memory-owner" not in row["stages"] and "memory_owner_sha256" not in row,
                "unexpected imported memory or owner for private profile")
    decode = result["decode"] = capture([args.decoder, guest], out, "decode", args.timeout)
    decode.update(stdout_sha256=digest(out / "decode.out"), stderr_sha256=digest(out / "decode.err"))
    require(decode.get("returncode") == 0, "qualification instruction decoder failed or timed out")
    with (out / "decode.out").open() as stream:
        header = stream.readline().rstrip("\n")
    prefix = f"MODULE {guest} "
    require(header.startswith(prefix), "decoder did not report this Core module")
    keys = {"bodies", "memtag_total", "threads_total", "shared_memories", "thread_spawn_imports", "eh_total", "tags"}
    counts = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)(?= |$)", header[len(prefix):]) if key in keys}
    result["opcodes"] = counts
    require(counts.keys() == keys and counts["bodies"] > 0 and counts["memtag_total"] == 0,
            "incomplete opcode decode or MTE instructions present")
    require(counts["shared_memories"] == int(target.threads)
            and (target.threads or not (counts["threads_total"] or counts["thread_spawn_imports"]))
            and (target.eh or not (counts["eh_total"] or counts["tags"]))
            and (not case.get("requires_eh") or counts["eh_total"] > 0), "instructions disagree with profile")
    return guest, owner


def saved_engine(row, original, engine, expected):
    data = {"comparison": "unavailable"}
    try:
        detail = stage_captures(original, row, engine)
        require(detail["argv"] == expected, f"{engine} argv differs from the reviewed profile and grants")
        data.update(detail, saved_verdict=row["runs"][engine])
        if type(detail.get("returncode")) != int or "timeout_seconds" in detail or detail["returncode"] < 0:
            data["reason"] = "original execution timed out, was signaled or has no exit code"
    except EVIDENCE_ERRORS as error:
        data["reason"] = f"original {engine} evidence: {error}"
    return data


def run_host(args, target, guest, owner, policy, out):
    options = []
    for index, token in enumerate(policy):
        if token == "--wasip1-single-interface":
            options.append(policy[index + 3] + "=" + policy[index + 2])
        elif token == "--wasip1-single-grant":
            options.append("grant=" + policy[index + 2])
    report = out / "host.log"
    argv = [args.host, str(target.bits), "eh" if target.eh else "noeh", guest, owner or "-", report, *options]
    result = capture(argv, out, "wasmtime", args.timeout)
    lines = report.read_text(errors="replace").splitlines() if report.is_file() else []
    started = "invoke _start" in lines
    result.update(start_invoked=started, stdout_sha256=digest(out / "wasmtime.out"), stderr_sha256=digest(out / "wasmtime.err"),
                  host_log_sha256=digest(report) if report.is_file() else None)
    last = lines[-1] if lines else ""
    end = re.fullmatch(r"end (returned|proc_exit) (\d+)", last)
    heading = ["wasmtime-c-api " + WASMTIME_VERSION, "memory " + ("env.memory" if owner else "caller.memory")]
    # Unsupported grants are rejected by the pinned adapter before it opens the engine.
    if not started and last.startswith(("error unexpected import ", "error unsupported WASIp1 import ",
            "error only the denied profile is implemented for ", "error unknown or duplicate grant")):
        result.update(termination="unsupported-import-or-grant", detail=last)
    elif "timeout_seconds" in result:
        result["termination"] = "timeout"
    elif result["returncode"] == 0 and lines[:2] == heading and started and end:
        result.update(termination=end[1], guest_exit_code=int(end[2]))
    else:
        result.update(termination="execution-error" if started else "setup-or-instantiation-error", detail=last)
    return result


def compare_guest(args, row, case, target, original, out, directory, result):
    guest, owner = inspect_guest(args, row, case, target, original, out, result)
    outside_policy = []
    for entry in result["imports"]:
        module, name = entry["module"], entry["name"]
        if target.threads and (module, name) in (("env", "memory"), ("wasi", "thread-spawn")):
            continue
        if module != "wasi_snapshot_preview1" or name.removesuffix("_wasm64") not in PERMISSIONS:
            outside_policy.append(f"{module}.{name}")
    if outside_policy:
        result["reason"] = "no reviewed matrix policy for " + ", ".join(outside_policy)
        return "unsupported-import-or-grant"
    commands = {}
    for engine in ENGINES:
        cmd = runtime_args(str(tool_path(args.tools, "u2ros")), engine, target, result["imports"],
                           str(directory / "owner.wasm") if owner else None, str(directory / "guest.wasm"),
                           thread_stack_mib=8, thread_storage_mib=64)
        commands[engine] = cmd
        result["engines"][engine] = saved_engine(row, original, engine, cmd)
    host = result["wasmtime"] = run_host(args, target, guest, owner, commands["int"], out)
    if "guest_exit_code" not in host:
        return host["termination"]
    pattern = case.get("stdout_pattern", re.escape(case.get("stdout", ""))).encode()
    host["expected_stdout"] = re.fullmatch(pattern, (out / "wasmtime.out").read_bytes()) is not None
    for entry in result["engines"].values():
        if "reason" in entry:
            continue
        entry["exit_equal"] = entry["returncode"] == host["guest_exit_code"]
        entry["stdout_equal"] = entry["stdout_sha256"] == host["stdout_sha256"]
        entry["stderr_equal"] = entry["stderr_sha256"] == host["stderr_sha256"]
        agrees = entry["exit_equal"] and entry["stdout_equal"] and entry["stderr_equal"]
        entry["comparison"] = "match" if agrees else "difference"
    if any(data["comparison"] == "difference" for data in result["engines"].values()):
        return "difference"
    if any(data["comparison"] == "unavailable" for data in result["engines"].values()):
        return "comparison-unavailable"
    if (row["status"] != "executed" or any(data["saved_verdict"] != "pass" for data in result["engines"].values())
            or host["guest_exit_code"] != 0 or not host["expected_stdout"]):
        return "guest-or-original-matrix-failed"
    return "match"


def replay(args, cases, records, key):
    name, profile = key
    case, target = cases[name], PROFILES[profile]
    original, out = (base / profile / name for base in (args.results, args.work))
    out.mkdir(parents=True)
    negative = diagnostic(case, target)
    result = {"case": name, "profile": profile, "language": case["language"], "kind": case["kind"],
              "project": case.get("project"), "vm": args.vm_identity, "planned_guest": negative is None,
              "engines": {engine: {"comparison": "unavailable"} for engine in ENGINES}}
    try:
        if key not in records:
            result.update(status="original-row-unavailable", reason="cell missing from original results")
        else:
            row = records[key]
            result["original_status"] = row["status"]
            info = original / "result.json"
            require(row == read_json(info), "per-cell receipt differs from results.jsonl")
            result["original_result_sha256"] = digest(info)
            require(row["vm"] == args.vm_identity and all(row[k] == result[k] for k in ("language", "kind", "project"))
                    and row["requires_eh"] == case.get("requires_eh", False), "original cell identity mismatch")
            runtime = runtime_receipt(args.sdks[case["language"]], target)
            require(all(row[k] == runtime[k] for k in ("runtime_receipt_sha256", "runtime_archives")),
                    "original runtime hashes disagree with installed SDK")
            result.update(runtime)
            if not negative and "wasm_sha256" not in row:
                result.update(status="original-module-unavailable", reason=row.get("error", row["status"]))
            else:
                directory = build_evidence(args, row, case, target, original, negative)
                if negative:
                    reason = f"missing {case['missing_header']}" if "missing_header" in case else "required EH is disabled"
                    result.update(status=negative[0], reason=reason, diagnostic_stage=negative[1],
                                  diagnostic=row["stages"][negative[1]])
                else:
                    result["status"] = compare_guest(args, row, case, target, original, out, directory, result)
    except EVIDENCE_ERRORS as error:
        result.update(status="evidence-error", reason=str(error))
    matrix.write_json(out / "result.json", result)
    return result


def main():
    cases = {case["id"]: case for case in read_json(HERE / "cases.json")}
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("results", "work", "host", "decoder", "vm", "objc-sdk", "objcpp-sdk", "wrwat"):
        parser.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    parser.add_argument("--host-sha256", required=True, help="trusted build digest of the pinned C API adapter")
    parser.add_argument("--matrix-policy", type=Path, default=matrix.CFAMILY / "sysroot_suite.py",
                        help="original matrix policy source, used as a digest witness")
    parser.add_argument("--case", action="append", choices=cases)
    parser.add_argument("--profile", action="append", choices=PROFILES)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    add_vm_identity_options(parser)
    args = parser.parse_args()
    if args.work == args.results or args.results in args.work.parents or min(args.jobs, args.timeout) < 1:
        parser.error("use a separate output directory and positive jobs and timeout")
    args.work.mkdir(parents=True, exist_ok=True)
    if any(args.work.iterdir()):
        parser.error("choose an empty output directory")
    inputs_file, results_file = (args.results / f for f in ("inputs.json", "results.jsonl"))
    inputs = read_json(inputs_file)
    args.vm_identity = verified_vm(args)
    require(inputs["vm"] == args.vm_identity, "original VM commit, tree, executable or receipt differs")
    checked_hash(HERE / "matrix.py", inputs["runner_sha256"])
    checked_hash(HERE / "cases.json", inputs["cases_sha256"])
    checked_hash(HERE / "upstreams.json", inputs["upstreams_sha256"])
    require(matrix.verify_sources() == inputs["upstreams"], "upstream manifest differs from original")
    sources = {str(p.relative_to(HERE)): digest(p) for folder in ("clients", "ports")
               for p in (HERE / folder).rglob("*") if p.is_file()}
    require(sources == inputs["sources"], "clients or port headers differ from original")
    args.sdks = {"objc": args.objc_sdk, "objcpp": args.objcpp_sdk}
    args.tools = original_tools(args, inputs)
    tool_path(args.tools, "u2ros")
    tool_path(args.tools, "imports reader")
    sys.path.insert(0, str(args.objc_sdk / "install"))
    import imports
    args.reader = imports
    plan = list(itertools.product(dict.fromkeys(args.case or cases), dict.fromkeys(args.profile or PROFILES)))
    original_plan = [tuple(key) for key in inputs["planned_cases"]]
    all_profiles = {*PROFILES, *(p.removesuffix("-nomte") + "-mte" for p in PROFILES)}
    declared = set(original_plan)
    require(len(declared) == len(original_plan) and all(case in cases and profile in all_profiles for case, profile in declared),
            "duplicate or unknown case/profile in original plan")
    records = {}
    for line in results_file.read_text().splitlines():
        row = json.loads(line)
        key = (row["case"], row["profile"])
        require(key in declared and key not in records, f"unplanned or duplicate original row {key}")
        records[key] = row
    meta = {"reference": "Wasmtime C API with the C-family qualification host", "reference_machine": platform.machine(),
            "wasmtime_version": WASMTIME_VERSION, "wasmtime_commit": WASMTIME_COMMIT, "vm": args.vm_identity,
            "host_binary_sha256": checked_hash(args.host, args.host_sha256),
            "host_source_sha256": digest(matrix.CFAMILY / "wasmtime_reference/host.cpp"),
            "decoder_sha256": digest(args.decoder), "driver_sha256": digest(Path(__file__)),
            "runtime_policy_sha256": digest(matrix.CFAMILY / "sysroot_suite.py"),
            "vm_target_sha256": digest(args.vm_target), "tools": args.tools,
            "original_inputs_sha256": digest(inputs_file), "original_results_sha256": digest(results_file),
            "cases_sha256": inputs["cases_sha256"], "upstreams_sha256": inputs["upstreams_sha256"],
            "matrix_sha256": inputs["runner_sha256"], "planned_cells": plan}
    matrix.write_json(args.work / "inputs.json", meta)
    scratch = args.work / "scratch"
    scratch.mkdir()
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch), LC_ALL="C", TZ="UTC")
    statuses, comparisons = Counter(), {engine: Counter() for engine in ENGINES}
    guests = starts = terminations = 0
    with (args.work / "results.jsonl").open("x") as log, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(lambda key: replay(args, cases, records, key), plan):
            print(json.dumps(result, sort_keys=True), file=log, flush=True)
            statuses[result["status"]] += 1
            if result["planned_guest"]:
                guests += 1
                host = result.get("wasmtime", {})
                starts += int(host.get("start_invoked", False))
                terminations += int("guest_exit_code" in host)
                for engine in ENGINES:
                    comparisons[engine][result["engines"][engine]["comparison"]] += 1
    complete = set(statuses) <= {"match", "eh-disabled-rejected", "dependency-unavailable"} and statuses["match"] == guests
    summary = {"vm": args.vm_identity, "planned_cells": len(plan), "planned_guests": guests, "guest_starts": starts,
               "guest_terminations": terminations, "statuses": statuses, "comparisons": comparisons,
               "inputs_sha256": digest(args.work / "inputs.json"), "results_sha256": digest(args.work / "results.jsonl"),
               "complete": complete}
    matrix.write_json(args.work / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
