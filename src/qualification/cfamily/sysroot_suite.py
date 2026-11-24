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
DEFAULT_ELF_RELOCATIONS = 65536
RELOCATION_CHARGE_BYTES = 512
ELF_HOSTS = {(2, 62, 0): "linux-x86_64", (1, 3, 0): "linux-i686", (2, 183, 0): "linux-aarch64",
             (1, 40, 0): "linux-arm", (1, 40, 0x200): "linux-arm", (1, 40, 0x400): "linux-armhf"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def vm_elf_host(path):
    """Select native code budgets using the VM binary, including the ARM float ABI."""
    with Path(path).open("rb") as stream:
        header = stream.read(64)
    if len(header) < 52 or header[:4] != b"\x7fELF" or header[5:7] != b"\x01\x01":
        raise ValueError(f"expected a little-endian Linux VM executable: {path}")
    machine = int.from_bytes(header[18:20], "little")
    float_abi = int.from_bytes(header[36:40], "little") & 0x600 if machine == 40 else 0
    return ELF_HOSTS.get((header[4], machine, float_abi))


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
            if limits.keys() - {"code_budget", "aot_stack_mib", "aot_relocations_by_host"}:
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
            if "aot_relocations_by_host" in limits:
                counts = limits["aot_relocations_by_host"]
                if not isinstance(counts, dict) or not counts or counts.keys() - set(ELF_HOSTS.values()):
                    raise ValueError(f"{label}: expected relocation counts keyed by Linux VM host")
                code_bytes = int(limits.get("code_budget", "67108864").split(":")[0].lstrip("0"))
                maximum = max(DEFAULT_ELF_RELOCATIONS, code_bytes // RELOCATION_CHARGE_BYTES)
                for host, count in counts.items():
                    if type(count) is not int or not 0 < count <= maximum:
                        raise ValueError(f"{label} {host}: expected an AOT relocation count in 1..{maximum}")


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
    case = case or {}
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
        profile = case.get("threaded_profiles", {}).get(target.name, {})
        code_budget = profile.get("code_budget", "67108864")
        thread_stack_mib = case.get("thread_stack_mib", thread_stack_mib)
        thread_storage_mib = case.get("thread_storage_mib", thread_storage_mib)
        if engine == "aot":
            thread_stack_mib = profile.get("aot_stack_mib", thread_stack_mib)
            if "aot_relocations_by_host" in profile:
                count = profile["aot_relocations_by_host"].get(vm_elf_host(vm))
                if count is not None:
                    code_budget += f",relocations={count}"
        cmd += ["--wasi-threads", "4", "16", str(thread_stack_mib * 1024**2), str(thread_storage_mib * 1024**2),
                code_budget, str(SHARED_MEMORY_PAGES * 65536),
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
        name = key[1].removesuffix("_wasm64")
        permissions = PERMISSIONS[name]
        if name == "poll_oneoff" and case.get("realtime_sleep"):
            # wasi-libc sleep(1) submits one relative CLOCK_REALTIME timer per call.
            permissions = ["realtime-timer"]
            cmd += ["--wasip1-single-limit", "main", "poll-subscriptions", "1",
                    "--wasip1-single-limit", "main", "poll.total-calls", "4",
                    "--enable-warning", "host_limited_wasip1." + key[1]]
        cmd += ["--wasip1-single-interface", "main", key[1], "allow" if permissions else "deny"]
        grants.update(permissions)
    for grant in sorted(grants):
        cmd += ["--wasip1-single-grant", "main", grant]
    return cmd + ["--run", wasm]


def missing_link_symbol(stderr, symbol):
    diagnostics = [line for line in stderr.splitlines() if re.search(r"\berror:", line, re.I)]
    return (len(diagnostics) == 2
            and re.fullmatch(r"wasm-ld: error: .+\.o: undefined symbol: " + re.escape(symbol), diagnostics[0]) is not None
            and diagnostics[1] == "clang: error: linker command failed with exit code 1 (use -v to see invocation)")


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
        symbol = case.get("unavailable_link_symbol")
        if (symbol and row["compile"].get("returncode") == 1
                and missing_link_symbol((out / "compile.err").read_text(errors="replace"), symbol)):
            row["missing_link_symbol"] = symbol
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
    if case.get("realtime_sleep"):
        poll_name = "poll_oneoff_wasm64" if target.bits == 64 else "poll_oneoff"
        if not any(i["module"] == "wasi_snapshot_preview1" and i["name"] == poll_name for i in imports):
            row["status"] = "missing-required-import"
            return row
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
        stdout = (out / (engine + ".out")).read_bytes()
        output = stdout.decode(errors="replace")
        if case.get("realtime_sleep"):
            stderr = (out / (engine + ".err")).read_text(errors="replace")
            diagnostic = re.search(r"\[(host_(?:denied|limited)_wasip1\.poll_oneoff(?:_wasm64)?)\]", stderr)
            if diagnostic:
                run["poll_policy_diagnostic"] = diagnostic[1]
        if "timeout_seconds" in run:
            verdict = "timeout"
        elif (target.threads and status == 126 and re.search(
                r"^uwvm: \[error\] WASI Threads [^\n]* exceeded a preparation resource limit \(per-child-storage=",
                (out / (engine + ".err")).read_text(errors="replace"), re.M)):
            verdict = "runtime-budget-rejected"
        elif status == 0 and "poll_policy_diagnostic" in run:
            verdict = "poll-policy-rejected"
        elif status == 0 and "pass_stdout_line" in case and case["pass_stdout_line"] not in output.splitlines():
            verdict = "output-mismatch"
        elif status == 0 and "expected_stdout" in case:
            expected = HERE / "upstream" / case["family"] / case["expected_stdout"]
            verdict = "pass" if stdout == expected.read_bytes() else "output-mismatch"
        elif status == 0 and "upstream_skip_stdout" in case:
            verdict = "upstream-skip" if stdout == case["upstream_skip_stdout"].encode() else "output-mismatch"
        elif "units" not in case and ((status == 0 and re.search(r"\bskipped\b", output, re.I))
                                      or (posix and status in (4, 5))):
            verdict = "upstream-skip"
        elif posix and status == 2:
            verdict = "upstream-unresolved"
        else:
            verdict = "pass" if status == 0 else "failed"
        row["runs"][engine] = {**run, "status": verdict}
    return row


def qualification_outcome(case, row):
    if row["status"] == "compile-failed" and "missing_link_symbol" in row:
        return "dependency-unavailable"
    if row["status"] != "linked" or row["runs"].keys() != {"int", "aot"}:
        return "failed"
    if "upstream_skip_stdout" in case and all(run["status"] == "upstream-skip" and run.get("returncode") == 0
                                              for run in row["runs"].values()):
        return "upstream-skip"
    if all(run["status"] == "pass" for run in row["runs"].values()):
        return "pass"
    return "failed"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("cc-sdk", "cxx-sdk", "compiler-sources", "vm", "wrwat", "decoder", "work"):
        p.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    p.add_argument("--suite", choices=("sysroot", "external"), default="sysroot")
    profiles = [Target(*v) for v in itertools.product((32, 64), (False, True), (False, True), (False, True))]
    p.add_argument("--case", action="append", metavar="SOURCE", help="select an exact manifest path (repeatable)")
    p.add_argument("--profile", action="append", choices=[t.name for t in profiles], help="select a profile (repeatable)")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--compile-timeout", type=int, default=180)
    p.add_argument("--run-timeout", type=int, default=180)
    add_vm_identity_options(p)
    args = p.parse_args()
    if min(args.jobs, args.compile_timeout, args.run_timeout) < 1:
        p.error("jobs and timeouts must be positive")
    vm = verified_vm(args)
    if args.work.exists() and any(args.work.iterdir()):
        p.error("choose an empty results directory to preserve previous evidence")
    manifest_file = HERE / ("external-libraries.json" if args.suite == "external" else "cases.json")
    manifest = json.loads(manifest_file.read_bytes())
    unknown = set(args.case or ()) - {c["path"] for c in manifest["cases"]}
    if unknown:
        p.error("unknown manifest path: " + ", ".join(sorted(unknown)))
    cases = [c for c in manifest["cases"] if not args.case or c["path"] in args.case]
    targets = [t for t in profiles if not args.profile or t.name in args.profile]
    entries = [(c, t) for c in cases for t in targets if t.threads or c["family"] != "Open POSIX"]
    if not entries:
        p.error("no selected case applies to the selected profiles")
    args.work.mkdir(parents=True, exist_ok=True)
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
    meta = {"vm": vm, "vm_sha256": vm["sha256"], "decoder_sha256": digest(args.decoder), "wrwat_sha256": digest(args.wrwat),
            "cc_sha256": digest(args.cc_sdk / "bin/wrc"), "cxx_sha256": digest(args.cxx_sdk / "bin/wrcc"),
            "runner_sha256": digest(Path(__file__)), "manifest_sha256": digest(manifest_file),
            "upstreams": manifest["upstreams"], "planned_builds": len(entries), "distinct_sources": len({c["path"] for c, t in entries})}
    if args.case or args.profile:
        meta["selection"] = {"sources": sorted({c["path"] for c, t in entries}), "profiles": sorted({t.name for c, t in entries})}
    (args.work / "inputs.json").write_text(json.dumps(meta, indent=2) + "\n")
    builds, runs, outcomes = Counter(), Counter(), Counter()
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
            row["qualification"] = qualification_outcome(case, row)
            outcomes[row["qualification"]] += 1
            print(json.dumps(row, separators=(",", ":")), file=log, flush=True)
            builds[row["status"]] += 1
            runs.update(r["status"] for r in row["runs"].values())
            if index % 100 == 0:
                print(index, len(entries), dict(builds), dict(runs), flush=True)
    exit_code = 0
    if outcomes["failed"]:
        exit_code = 1
    elif outcomes["pass"] != len(entries):
        exit_code = 77
    summary = {**meta, "builds": dict(builds), "executions": dict(runs),
               "qualification": dict(outcomes), "exit_code": exit_code}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
