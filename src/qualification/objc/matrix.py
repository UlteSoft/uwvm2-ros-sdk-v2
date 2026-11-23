#!/usr/bin/env python3
"""Build real Objective-C library members with installed SDKs and execute their client programs."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
CFAMILY = HERE.parent / "cfamily"
sys.path.insert(0, str(CFAMILY))
from sysroot_suite import SHARED_MEMORY_PAGES, Target, add_vm_identity_options, capture, digest, runtime_args, verified_vm

DRIVERS = {"objc": "wroc", "objcpp": "wrocxx"}
EXPECTED_RESULTS = {"executed", "eh-disabled-rejected", "dependency-unavailable"}
EXCEPTION_DIAGNOSTIC = re.compile(r"error: cannot use '(?:@try|@throw|try|throw)' with (?:Objective-C )?exceptions disabled")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def verify_sources():
    upstreams = json.loads((HERE / "upstreams.json").read_bytes())
    for name, project in upstreams.items():
        if not re.fullmatch(r"[0-9a-f]{40}", project["revision"]):
            raise ValueError(f"invalid Git revision for {name}")
        directory = HERE / "upstream" / name
        expected_files = project["files"]
        actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
        if actual_files != expected_files.keys() or not set(project["license_files"]) <= actual_files:
            raise ValueError(f"upstream file inventory mismatch for {name}")
        for relative, expected in expected_files.items():
            data = (directory / relative).read_bytes()
            header = f"blob {len(data)}\0".encode()
            if (hashlib.sha1(header + data).hexdigest() != expected["git_blob"]
                    or hashlib.sha256(data).hexdigest() != expected["sha256"]):
                raise ValueError(f"upstream file hash mismatch: {name}/{relative}")
    return upstreams


def tool_command(sdk, case, target):
    cmd = [sdk / "bin" / DRIVERS[case["language"]], "--platform", "generic", "--target", f"wasm{target.bits}",
           "--core", "3.0", "--threads" if target.threads else "--no-threads", "--eh" if target.eh else "--no-eh",
           "--mte" if target.mte else "--no-mte", "-O1"]
    for inc in case.get("includes", []):
        cmd.extend(["-I", HERE / inc])
    for define in case.get("defines", []):
        cmd.extend(["-D", define])
    return cmd


def gnustep_sources(case, sdk, out):
    # Upstream tests use ../objc from their own tree. Put the verbatim test
    # files next to the installed public headers, including generated objc-config.h.
    project = HERE / "upstream/libobjc2"
    tree = out / "libobjc2"
    tests = tree / "Test"
    tests.mkdir(parents=True)
    (tree / "objc").symlink_to(sdk / "include/sysroot/objc", target_is_directory=True)
    for relative in ["Test/Test.h", *case["units"]]:
        shutil.copyfile(project / relative, tree / relative)
    return [tree / rel for rel in case["units"]]


def record_stage(row, out, name, command, timeout):
    result = capture(command, out, name, timeout)
    result["stdout_sha256"] = digest(out / (name + ".out"))
    result["stderr_sha256"] = digest(out / (name + ".err"))
    row["stages"][name] = result
    return result


def build_status(out, stage, result, expected_error=None, rejection=None):
    if "timeout_seconds" in result:
        return stage + "-timeout"
    if result["returncode"] == 0:
        return "unexpected-acceptance" if expected_error else None
    if expected_error:
        # Native Clang can invoke both cc1 and the linker. Only the expected
        # compiler diagnostic on this source qualifies as a negative control.
        errors = (out / (stage + ".err")).read_text(errors="replace").splitlines()
        diagnostics = [line for line in errors if re.search(r"\b(?:fatal )?error:", line)]
        if diagnostics and all(expected_error.search(line) for line in diagnostics):
            return rejection
    return stage + "-failed"


def execute(args, case, target, wasm, out, row, inspect):
    widths = []
    imports = list(inspect(wasm.read_bytes(), memory_types=widths, memory_limits=True))
    row["imports"] = imports
    if widths != [target.bits]:
        return "memory-width-mismatch"
    owner = None
    if target.threads:
        memories = [entry for entry in imports if entry["kind"] == 2]
        if len(memories) != 1 or (memories[0]["module"], memories[0]["name"]) != ("env", "memory"):
            return "shared-memory-mismatch"
        flags, minimum, maximum = memories[0]["limits"]
        if flags != (7 if target.bits == 64 else 3) or not 0 < minimum <= maximum == SHARED_MEMORY_PAGES:
            return "shared-memory-mismatch"
        wat, owner = out / "owner.wat", out / "owner.wasm"
        width = "i64 " if target.bits == 64 else ""
        wat.write_text(f'(module (memory (export "memory") {width}{minimum} {maximum} shared))\n')
        result = record_stage(row, out, "memory-owner", [args.wrwat, wat, "--target", f"wasm{target.bits}",
                              "--core", "3.0", "--threads", "-o", owner], args.compile_timeout)
        failure = build_status(out, "memory-owner", result)
        if failure:
            return failure
        row["memory_owner_sha256"] = digest(owner)
    pattern = case.get("stdout_pattern", re.escape(case.get("stdout", ""))).encode()
    for engine in ("int", "aot"):
        argv = runtime_args(args.vm, engine, target, imports, owner, wasm, thread_stack_mib=8, thread_storage_mib=64)
        result = record_stage(row, out, engine, argv, args.run_timeout)
        if "timeout_seconds" in result:
            status = "timeout"
        elif result["returncode"] != 0:
            status = "guest-or-vm-failed"
        elif not re.fullmatch(pattern, (out / (engine + ".out")).read_bytes()):
            status = "output-mismatch"
        else:
            status = "pass"
        row["runs"][engine] = status
    return "executed" if all(status == "pass" for status in row["runs"].values()) else "runtime-failed"


def build_case(args, case, target, out, row, inspect):
    sdk = args.sdks[case["language"]]
    cmd = tool_command(sdk, case, target)
    triple = f"wasm{target.bits}-wasip1" + ("-threads" if target.threads else "")
    flavor = "core3.0-" + ("eh" if target.eh else "noeh") + ("-mte" if target.mte else "-nomte")
    receipt = sdk / "share/uwros/objc" / triple / flavor / "runtime.json"
    row["runtime_receipt_sha256"] = digest(receipt)
    row["runtime_archives"] = {name: digest(sdk / "lib" / triple / flavor / name) for name in ("libobjc.a", "libuwrosobjc.a")}
    if "member" in case:
        member = HERE / case["member"]
        obj = out / "member.o"
        result = record_stage(row, out, "compile-member", [*cmd, "-c", member, "-o", obj], args.compile_timeout)
        header = case.get("missing_header")
        expected = re.compile(r"fatal error: '" + re.escape(header) + "' file not found") if header else None
        status = build_status(out, "compile-member", result, expected, "dependency-unavailable")
        if status:
            return status
        row["member_sha256"] = digest(obj)
        archive = out / "component.a"
        ar = sdk / "share/toolchains/portable/bin/llvm-ar"
        result = record_stage(row, out, "archive", [ar, "rcsD", archive, obj], args.compile_timeout)
        status = build_status(out, "archive", result)
        if status:
            return status
        row["archive_sha256"] = digest(archive)
        sources = [HERE / case["client"], archive]
    elif "units" in case:
        sources = gnustep_sources(case, sdk, out)
    else:
        sources = [HERE / case["client"]]

    if case.get("requires_eh") and not target.eh:
        # Isolate the C/ObjC++ compiler phase for all negative cases. A link
        # failure or a general build failure is a different result.
        result = record_stage(row, out, "compile-noeh", [*cmd, "-c", sources[0], "-o", out / "noeh.o"], args.compile_timeout)
        return build_status(out, "compile-noeh", result, EXCEPTION_DIAGNOSTIC, "eh-disabled-rejected")
    wasm = out / "guest.wasm"
    if target.threads:
        cmd.extend(["--shared-memory-pages", str(SHARED_MEMORY_PAGES)])
    result = record_stage(row, out, "link", [*cmd, *sources, "-o", wasm], args.compile_timeout)
    status = build_status(out, "link", result)
    if status:
        return status
    row["wasm_sha256"] = digest(wasm)
    return execute(args, case, target, wasm, out, row, inspect)


def run_case(args, case, target, inspect):
    out = args.work / target.name / case["id"]
    out.mkdir(parents=True, exist_ok=False)
    row = {"vm": args.vm_identity, "case": case["id"], "kind": case["kind"], "language": case["language"], "profile": target.name,
           "project": case.get("project"), "requires_eh": case.get("requires_eh", False), "stages": {}, "runs": {}}
    try:
        row["status"] = build_case(args, case, target, out, row, inspect)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        row.update(status="harness-error", error=repr(exc))
    write_json(out / "result.json", row)
    return row


def main():
    cases = json.loads((HERE / "cases.json").read_bytes())
    profiles = [Target(*parts) for parts in itertools.product((32, 64), (False, True), (False, True), (False, True))]
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("objc-sdk", "objcpp-sdk", "vm", "wrwat", "work"):
        parser.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--case", action="append", choices=[case["id"] for case in cases])
    parser.add_argument("--profile", action="append", choices=[target.name for target in profiles])
    parser.add_argument("--compile-timeout", type=int, default=180)
    parser.add_argument("--run-timeout", type=int, default=180)
    add_vm_identity_options(parser)
    args = parser.parse_args()
    args.vm_identity = verified_vm(args)
    if min(args.jobs, args.compile_timeout, args.run_timeout) < 1:
        parser.error("job counts and timeouts must be positive")
    if args.work.exists() and any(args.work.iterdir()):
        parser.error("use an empty --work directory to keep existing results")
    args.work.mkdir(parents=True, exist_ok=True)
    scratch = args.work / "scratch"
    scratch.mkdir()
    os.environ.update(TMPDIR=str(scratch), TEMP=str(scratch), TMP=str(scratch), PYTHONDONTWRITEBYTECODE="1", LC_ALL="C", TZ="UTC")
    args.sdks = {"objc": args.objc_sdk, "objcpp": args.objcpp_sdk}
    sys.path.insert(0, str(args.objc_sdk / "install"))
    from imports import inspect
    upstreams = verify_sources()
    planned = [(case, target) for case in cases for target in profiles if (not args.case or case["id"] in args.case)
               and (not args.profile or target.name in args.profile)]
    inputs = {str(p.relative_to(HERE)): digest(p) for base in ("clients", "ports") for p in (HERE / base).rglob("*") if p.is_file()}
    tools = {"u2ros": args.vm, "wrwat": args.wrwat, "C-family runner": CFAMILY / "sysroot_suite.py",
             "imports reader": args.objc_sdk / "install/imports.py"}
    for lang, sdk in args.sdks.items():
        tools[DRIVERS[lang]] = sdk / "bin" / DRIVERS[lang]
        tools[lang + " llvm-ar"] = sdk / "share/toolchains/portable/bin/llvm-ar"
    expected_executions = sum(case["kind"] != "dependency-probe" and (target.eh or not case.get("requires_eh"))
                              for case, target in planned)
    write_json(args.work / "inputs.json", {"vm": args.vm_identity, "upstreams": upstreams, "sources": inputs, "runner_sha256": digest(Path(__file__)),
               "cases_sha256": digest(HERE / "cases.json"), "upstreams_sha256": digest(HERE / "upstreams.json"),
               "tools": {label: {"path": str(p), "sha256": digest(p)} for label, p in tools.items()},
               "planned_cases": [[case["id"], target.name] for case, target in planned], "planned_engine_runs": expected_executions * 2})
    results, engines = Counter(), Counter()
    with (args.work / "results.jsonl").open("x") as log, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_case, args, case, target, inspect) for case, target in planned]
        for task in as_completed(futures):
            row = task.result()
            print(json.dumps(row, separators=(",", ":")), file=log, flush=True)
            print(row["case"], row["profile"], row["status"], flush=True)
            results[row["status"]] += 1
            engines.update(row["runs"].values())
    ok = set(results) <= EXPECTED_RESULTS and results["executed"] == expected_executions and engines["pass"] == 2 * expected_executions
    write_json(args.work / "summary.json", {"vm": args.vm_identity, "success": ok, "planned": len(planned), "planned_engine_runs": expected_executions * 2,
               "results": dict(results), "engine_runs": dict(engines)})
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
