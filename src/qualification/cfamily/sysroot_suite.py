#!/usr/bin/env python3
"""Compile library tests with installed WROS frontends and run each Wasm on both u2ros engines."""
import argparse
import hashlib
import itertools
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERMISSIONS = {
    "args_get": ["args"], "args_sizes_get": ["args"],
    "environ_get": ["environ"], "environ_sizes_get": ["environ"],
    "poll_oneoff": [],
    "proc_exit": ["proc-exit"],
    "clock_time_get": ["monotonic-clock"],
    "clock_res_get": ["monotonic-resolution"],
    "sched_yield": ["sched-yield"],
    "fd_write": ["stdout.write", "stderr.write"],
    "fd_fdstat_get": ["stdio.metadata"],
    "fd_close": [], "fd_seek": [], "fd_read": [], "fd_pread": [],
    "fd_prestat_get": [], "fd_prestat_dir_name": [],
}
SHARED_MEMORY_PAGES = 128
MAX_LLVM_IR_INSTRUCTIONS = 4194304
MAX_LLVM_BASIC_BLOCKS = 1048576


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def add_vm_identity_options(parser):
    parser.add_argument("--vm-receipt", type=Path, help="VM build receipt or installed share/host-tools/origins.json")
    parser.add_argument("--vm-target", type=Path, default=HERE.parent.parent.parent / "document/qualification/runtime-qualification.json",
                        help="reviewed matrix pin with vm_commit and vm_tree")


def verified_vm(args):
    """Bind the actual executable to the exact revision selected for this matrix."""
    target = json.loads(args.vm_target.read_bytes())
    receipt = args.vm_receipt or args.vm.parent / "receipt.json"
    if args.vm_receipt is None and not receipt.exists():
        receipt = args.vm.parent.parent / "share/host-tools/origins.json"
    raw = receipt.read_bytes()
    record = json.loads(raw)
    record = record.get("uwvm2-ros", record)
    vm_hash = digest(args.vm)
    if (not all(re.fullmatch("[0-9a-f]{40}", target[field]) for field in ("vm_tree", "vm_commit"))
            or (record.get("commit"), record.get("tree")) != (target["vm_commit"], target["vm_tree"])
            or record.get("vm_sha256", record.get("sha256")) != vm_hash):
        raise ValueError("VM executable or build receipt differs from the accepted matrix revision")
    return {"commit": record["commit"], "tree": record["tree"], "sha256": vm_hash,
            "receipt_sha256": hashlib.sha256(raw).hexdigest()}


@dataclass(frozen=True)
class Target:
    bits: int
    threads: bool
    mte: bool
    eh: bool

    @property
    def name(self):
        triple = f"wasm{self.bits}-wasip1" + ("-threads" if self.threads else "")
        return triple + ("-eh" if self.eh else "-noeh") + ("-mte" if self.mte else "-nomte")


def validate_thread_budgets(cases):
    threaded = {Target(bits, True, mte, eh).name for bits, mte, eh in
                itertools.product((32, 64), (False, True), (False, True))}
    for case in cases:
        overrides = case.get("threaded_profiles", {})
        if not isinstance(overrides, dict):
            raise ValueError(f"{case['path']}: threaded_profiles must be a profile map")
        for profile, limits in overrides.items():
            label = f"{case['path']} ({profile})"
            if profile not in threaded or not isinstance(limits, dict) or not limits:
                raise ValueError(f"{label}: invalid threaded profile or empty limits")
            if limits.keys() - {"code_budget", "aot_stack_mib"}:
                raise ValueError(f"{label}: unknown threaded budget field")
            if "aot_stack_mib" in limits:
                stack = limits["aot_stack_mib"]
                if type(stack) is not int or not 0 < stack * 1024**2 <= 2 * sys.maxsize:
                    raise ValueError(f"{label}: expected a positive finite AOT stack size in MiB")
            if "code_budget" in limits:
                code = limits["code_budget"]
                fields = code.split(":") if isinstance(code, str) else []
                maxima = (2 * sys.maxsize, MAX_LLVM_IR_INSTRUCTIONS, MAX_LLVM_BASIC_BLOCKS)
                if not 1 <= len(fields) <= len(maxima):
                    raise ValueError(f"{label}: expected CODE[:INSTRUCTIONS[:BLOCKS]]")
                for field, maximum in zip(fields, maxima):
                    digits = field.lstrip("0")
                    if (not re.fullmatch(r"[0-9]+", digits) or len(digits) > len(str(maximum))
                            or int(digits) > maximum):
                        raise ValueError(f"{label}: expected a decimal count in 1..{maximum}, got {field!r}")


def capture(command, directory, name, timeout):
    argv = list(map(str, command))
    output, errors = directory / (name + ".out"), directory / (name + ".err")
    with output.open("wb") as stdout, errors.open("wb") as stderr:
        try:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout)
            result = {"returncode": proc.returncode}
        except subprocess.TimeoutExpired:
            result = {"timeout_seconds": timeout}
    return {**result, "argv": argv}


def runtime_args(vm, engine, target, imports, owner, wasm, *, case=None, thread_stack_mib=1, thread_storage_mib=16):
    cmd = [vm, "--runtime-" + engine, "--runtime-compile-threads", "0",
           "--debug-fault-action", "exit", "--wasm-feature-wasm3",
           "--wasm-feature-" + ("enable" if target.threads else "disable") + "-threads",
           "--wasm-feature-" + ("enable" if target.eh else "disable") + "-exceptions"]
    if target.bits == 64:
        cmd += ["--wasm-feature-enable-memory64", "--wasm-feature-enable-table64"]
    if target.mte:
        cmd += ["--runtime-memtag-mode", "sync"]
    else:
        cmd += ["--wasm-feature-disable-memtag-extension", "--runtime-disable-memtag"]
    if engine == "aot":
        cmd += ["--runtime-llvm-jit-cache-path", "disable", "--runtime-llvm-jit-policy", "fast-compile"]
    cmd += ["--wasm-set-main-module-name", "main", "--wasip1-single-create", "main",
            "--wasip1-single-enable", "main", "--wasip1-single-hide-host-api", "main",
            "--wasip1-single-noinherit-system-environment", "main"]
    if target.threads:
        case = case or {}
        profile = case.get("threaded_profiles", {}).get(target.name, {})
        thread_stack_mib = case.get("thread_stack_mib", thread_stack_mib)
        thread_storage_mib = case.get("thread_storage_mib", thread_storage_mib)
        if engine == "aot":
            thread_stack_mib = profile.get("aot_stack_mib", thread_stack_mib)
        cmd += ["--wasi-threads", "4", "16", str(thread_stack_mib * 1024**2), str(thread_storage_mib * 1024**2),
                profile.get("code_budget", "67108864"), str(SHARED_MEMORY_PAGES * 65536),
                "--wasithread-single-create", "main", "--wasithread-single-enable", "main",
                "--wasithread-single-interface", "main", "thread-spawn", "allow",
                "--wasithread-single-limit", "main", "max-extra-threads", "4",
                "--wasithread-single-limit", "main", "max-spawns", "16",
                "--wasm-preload-library", owner, "env"]
    grants = set()
    for item in imports:
        key = item["module"], item["name"]
        if target.threads and key in (("env", "memory"), ("wasi", "thread-spawn")):
            continue
        if key[0] != "wasi_snapshot_preview1":
            raise ValueError(f"unexpected host import {key}")
        permissions = PERMISSIONS[key[1].removesuffix("_wasm64")]
        cmd += ["--wasip1-single-interface", "main", key[1], "allow" if permissions else "deny"]
        grants.update(permissions)
    for grant in sorted(grants):
        cmd += ["--wasip1-single-grant", "main", grant]
    return cmd + ["--run", wasm]


def check_case(args, case, target, inspect):
    path = Path(case["path"])
    posix = case["family"] == "Open POSIX"
    cxx = case.get("language") == "cpp" or case["family"] == "libc++"
    source = (args.compiler_sources if posix and "sdk_case" not in case else HERE) / path
    out = args.work / target.name / case["family"] / path.parent.name / path.name
    out.mkdir(parents=True, exist_ok=True)
    row = {"profile": target.name, "family": case["family"], "source": path.as_posix(),
           "source_sha256": digest(source), "runs": {}}
    wasm = out / "guest.wasm"
    sdk = args.cxx_sdk if cxx else args.cc_sdk
    cmd = [sdk / "bin" / ("wrcc" if cxx else "wrc"), "--target", f"wasm{target.bits}",
           "--core", "3.0", "--std", "c++20" if cxx else "c17", "-O1",
           "--mte" if target.mte else "--no-mte", "--eh" if target.eh else "--no-eh",
           "--threads" if target.threads else "--no-threads", "--build-receipt"]
    if target.threads:
        cmd += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)]
    sources = [source]
    if "units" in case:
        project = HERE / "upstream" / case["family"]
        sources.extend(project / unit for unit in case["units"])
        for include in case["includes"]:
            cmd.extend(("-I", project / include))
        defines = list(case.get("defines", []))
        if not target.eh:
            defines.extend(case.get("noeh_defines", []))
        for define in defines:
            cmd.extend(("-D", define))
        inc = None
    elif posix:
        cmd += ["-D", "_POSIX_C_SOURCE=200809L", "-D", "_WASI_EMULATED_SIGNAL",
                "-lwasi-emulated-signal", "-lwasi-emulated-getpid"]
        inc = args.compiler_sources / "wasi-libc/test/open-posix-test-suite/include"
    elif case["family"] == "libc-test":
        inc = HERE / "upstream/libc-test/src/common"
        sources += [inc / name for name in ("print.c", "path.c", "rand.c", "utf8.c")]
        cmd += ["-D", "_GNU_SOURCE"]
    elif cxx:
        if "ADDITIONAL_COMPILE_FLAGS(has-fconstexpr-steps): -fconstexpr-steps=20000000" in source.read_text():
            cmd += ["--constexpr-steps", "20000000"]
        inc = HERE / "upstream/llvm/libcxx/test/support"
    else:
        inc = args.compiler_sources / "llvm-project/compiler-rt/lib/builtins"
    if inc is not None:
        cmd.extend(("-I", inc))
    row["compile"] = capture(cmd + [*sources, "-o", wasm], out, "compile", args.compile_timeout)
    if row["compile"].get("returncode") != 0:
        row["status"] = "compile-timeout" if "timeout_seconds" in row["compile"] else "compile-failed"
        return row
    receipt = json.loads((out / "guest.wasm.wros-build.json").read_bytes())
    row["wasm_sha256"] = digest(wasm)
    if row["wasm_sha256"] != receipt["artifact_sha256"]:
        raise ValueError("compiler receipt digest mismatch")
    row["compiler_sha256"] = receipt["compiler_sha256"]
    row["decode"] = capture([args.decoder, wasm], out, "decode", args.compile_timeout)
    if row["decode"].get("returncode") != 0:
        row["status"] = "decode-failed"
        return row
    header = (out / "decode.out").read_text().splitlines()[0]
    counts = dict((k, int(v)) for k, v in re.findall(r" (memtag_total|threads_total|shared_memories|thread_spawn_imports|eh_total|tags)=(\d+)", header))
    row["opcodes"] = counts
    widths = []
    imports = list(inspect(wasm.read_bytes(), memory_limits=target.threads, memory_types=widths))
    row["imports"] = imports
    if (len(counts) != 6 or widths != [target.bits] or (not target.mte and counts["memtag_total"])
            or (not target.eh and (counts["eh_total"] or counts["tags"]))
            or (not target.threads and (counts["threads_total"] or counts["shared_memories"] or counts["thread_spawn_imports"]))
            or (target.threads and counts["shared_memories"] != 1)):
        row["status"] = "feature-mismatch"
        return row
    owner = None
    if target.threads:
        memory, = [item for item in imports if item["kind"] == 2]
        flags, minimum, maximum = memory["limits"]
        if ((memory["module"], memory["name"]) != ("env", "memory")
                or flags != (7 if target.bits == 64 else 3)
                or not 0 < minimum <= maximum == SHARED_MEMORY_PAGES):
            row["status"] = "feature-mismatch"
            return row
        # dlmalloc starts at the linked heap bounds, then requests pages with memory.grow.
        wat, owner = out / "owner.wat", out / "owner.wasm"
        width = "i64 " if target.bits == 64 else ""
        wat.write_text(f'(module (memory (export "memory") {width}{minimum} {maximum} shared))\n')
        build = capture([args.wrwat, wat, "--target", f"wasm{target.bits}", "--core", "3.0", "--threads",
                         "-o", owner], out, "owner", args.compile_timeout)
        row["memory_owner"] = build
        if build.get("returncode") != 0:
            row["status"] = "owner-timeout" if "timeout_seconds" in build else "owner-failed"
            return row
        build["sha256"] = digest(owner)
    row["status"] = "linked"
    for engine in ("int", "aot"):
        argv = runtime_args(args.vm, engine, target, imports, owner, wasm, case=case)
        run = capture(argv, out, engine, args.run_timeout)
        status = run.get("returncode")
        output = (out / (engine + ".out")).read_text(errors="replace")
        if "timeout_seconds" in run:
            verdict = "timeout"
        elif (target.threads and status == 126 and re.search(
                r"^uwvm: \[error\] WASI Threads [^\n]* exceeded a preparation resource limit \(per-child-storage=",
                (out / (engine + ".err")).read_text(errors="replace"), re.M)):
            verdict = "runtime-budget-rejected"
        elif status == 0 and "expected_stdout" in case:
            expected = HERE / "upstream" / case["family"] / case["expected_stdout"]
            verdict = "pass" if (out / (engine + ".out")).read_bytes() == expected.read_bytes() else "output-mismatch"
        elif "units" not in case and ((status == 0 and re.search(r"\bskipped\b", output, re.I))
                                      or (posix and status in (4, 5))):
            verdict = "upstream-skip"
        elif posix and status == 2:
            verdict = "upstream-unresolved"
        else:
            verdict = "pass" if status == 0 else "failed"
        row["runs"][engine] = {**run, "status": verdict}
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("cc-sdk", "cxx-sdk", "compiler-sources", "vm", "wrwat", "decoder", "work"):
        p.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    p.add_argument("--suite", choices=("sysroot", "external"), default="sysroot")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--compile-timeout", type=int, default=180)
    p.add_argument("--run-timeout", type=int, default=180)
    add_vm_identity_options(p)
    args = p.parse_args()
    vm = verified_vm(args)
    if args.work.exists() and any(args.work.iterdir()):
        p.error("choose an empty results directory to preserve previous evidence")
    args.work.mkdir(parents=True, exist_ok=True)
    manifest_file = HERE / ("external-libraries.json" if args.suite == "external" else "cases.json")
    manifest = json.loads(manifest_file.read_bytes())
    validate_thread_budgets(manifest["cases"])
    if args.suite == "external":
        upstream_hashes = {name: repo["git_blobs"] for name, repo in manifest["upstreams"].items()}
    else:
        upstream_hashes = {"llvm": manifest["llvm_git_blobs"], "libc-test": manifest["libc_test_git_blobs"]}
    for project, hashes in upstream_hashes.items():
        for rel, expected in hashes.items():
            data = (HERE / "upstream" / project / rel).read_bytes()
            if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != expected:
                raise ValueError(f"upstream source digest mismatch: {rel}")
    sys.path.insert(0, str(args.cc_sdk / "install"))
    from imports import inspect
    profiles = [Target(*v) for v in itertools.product((32, 64), (False, True), (False, True), (False, True))]
    entries = [(case, t) for case in manifest["cases"] for t in profiles if t.threads or case["family"] != "Open POSIX"]
    meta = {"vm": vm, "vm_sha256": vm["sha256"], "decoder_sha256": digest(args.decoder), "wrwat_sha256": digest(args.wrwat),
            "cc_sha256": digest(args.cc_sdk / "bin/wrc"), "cxx_sha256": digest(args.cxx_sdk / "bin/wrcc"),
            "runner_sha256": digest(Path(__file__)), "manifest_sha256": digest(manifest_file),
            "upstreams": manifest["upstreams"], "planned_builds": len(entries), "distinct_sources": len(manifest["cases"])}
    (args.work / "inputs.json").write_text(json.dumps(meta, indent=2) + "\n")
    builds, runs = Counter(), Counter()
    with (args.work / "results.jsonl").open("x") as log, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        tasks = {pool.submit(check_case, args, c, t, inspect): (c, t) for c, t in entries}
        for index, task in enumerate(as_completed(tasks), 1):
            case, target = tasks[task]
            try:
                row = task.result()
            except Exception as exc:
                row = {"profile": target.name, "family": case["family"], "source": case["path"],
                       "status": "harness-error", "error": repr(exc), "runs": {}}
            if "sdk_case" in case:
                row["sdk_case"] = case["sdk_case"]
            row["vm"] = vm
            print(json.dumps(row, separators=(",", ":")), file=log, flush=True)
            builds[row["status"]] += 1
            runs.update(r["status"] for r in row["runs"].values())
            if index % 100 == 0:
                print(index, len(entries), dict(builds), dict(runs), flush=True)
    summary = {**meta, "builds": dict(builds), "executions": dict(runs)}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return 0 if builds == {"linked": len(entries)} and runs == {"pass": 2 * len(entries)} else 1


if __name__ == "__main__":
    sys.exit(main())
