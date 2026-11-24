#!/usr/bin/env python3
"""Build production SDK workloads and compare paired, in-guest execution times on one Linux host."""
import argparse
from collections import Counter
import itertools
import json
import os
from pathlib import Path
import platform
import re
import resource
import statistics
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from engines import EXTERNAL, NATIVE_WASMTIME, capability, observation, references
from optional_isa_suite import LANGUAGES, TARGETS
from sysroot_suite import add_vm_identity_options, digest, verified_vm, vm_elf_host
from workloads import ROOT, WORKLOADS, build, expected, public_inputs, require, sdk_identity

HOSTS = ("linux-x86_64", "linux-i686", "linux-aarch64", "linux-arm", "linux-armhf")


def selected(args):
    for host, language, target, simd in itertools.product(
            [args.host] if args.host else HOSTS, [args.language] if args.language else LANGUAGES, TARGETS, (False, True)):
        if args.profile and args.profile != target.name:
            continue
        if args.width and args.width != target.bits:
            continue
        if any(value is not None and (value == "on") != setting for value, setting in
               ((args.eh, target.eh), (args.threads, target.threads), (args.mte, target.mte), (args.simd, simd))):
            continue
        yield host, language, target, simd


def cell_key(host, language, target, simd):
    return {"host": host, "language": language, "workload": WORKLOADS[language].name, "profile": target.name,
            "guest_bits": target.bits, "eh": target.eh, "threads": target.threads, "mte": target.mte, "simd": simd}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def spread(values):
    lower, _, upper = statistics.quantiles(values, n=4, method="inclusive")
    return {"n": len(values), "min": min(values), "q1": lower, "median": statistics.median(values),
            "q3": upper, "max": max(values)}


def pair(args, row, target, simd, guest, owner, out, reference):
    warm = row["correctness"]
    for name in ("int", "aot", reference):
        if warm[name]["status"] != "pass":
            return {"status": warm[name]["status"], "reason": f"{name}: " + warm[name]["reason"]}
    if args.correctness_only or args.environment == "user-qemu":
        return {"status": "unavailable", "reason": "correctness-only execution environment or selection"}
    if reference.startswith("wasmtime-") and args.host not in NATIVE_WASMTIME:
        return {"status": "unavailable", "reason": "32-bit Wasmtime/Pulley has no native Cranelift backend for this host"}
    if reference == "wasmtime-host" and not warm[reference]["native_backend_verified"]:
        return {"status": "unavailable", "reason": "C API adapter lacks verified native target; build native-wasmtime-host.cpp"}
    if (reference == "wavm" and not args.references[reference]["static"]
            and "library" not in args.references[reference]):
        return {"status": "unavailable", "reason": "dynamic WAVM runtime library could not be identified"}
    samples, ratios = [], []
    sides = ("aot", reference)
    for index in range(args.samples):
        order = sides if index % 2 == 0 else sides[::-1]
        sample = {"order": order, "runs": {}}
        samples.append(sample)
        for name in order:
            directory = out / ("aot-vs-" + reference) / f"pair-{index + 1:02d}" / name
            run = sample["runs"][name] = observation(args, row, name, target, simd, guest, owner, directory)
            if run["status"] != "pass":
                return {"status": run["status"], "reason": f"{name}: " + run["reason"], "samples": samples}
            if name == "wasmtime-host" and not run["native_backend_verified"]:
                return {"status": "failed", "reason": "C API native backend changed after warmup", "samples": samples}
        ns = sample["runs"]
        sample["aot_over_reference"] = ns["aot"]["guest_ns"] / ns[reference]["guest_ns"]
        ratios.append(sample["aot_over_reference"])
    result = {"status": "measured", "samples": samples, "aot_over_reference": spread(ratios),
              "guest_nanoseconds": {name: spread([s["runs"][name]["guest_ns"] for s in samples]) for name in sides}}
    if reference == "aot-disabled":
        result["within_1_5_target"] = statistics.median(ratios) <= 1.5
    return result


def run_cell(args, host, language, target, simd, inspect, uleb):
    row = cell_key(host, language, target, simd)
    out = args.work / language / target.name / ("simd-on" if simd else "simd-off")
    out.mkdir(parents=True)
    row.update(directory=str(out.relative_to(args.work)), expected=expected(language), correctness={}, comparisons={})
    try:
        guest, owner = build(args, row, out, target, simd, inspect, uleb)
        external = ("wavm",) if target.mte else ("wasmtime-host", "wasmtime-cli")
        others = (*external, "aot-disabled") if target.mte else external
        for name in ("int", "aot", *others):
            reason = capability(args, name, target, row["imports"]) if name in EXTERNAL else None
            row["correctness"][name] = ({"status": "unavailable", "reason": reason} if reason else
                observation(args, row, name, target, simd, guest, owner, out / "correctness" / name))
        for name in others:
            row["comparisons"][name] = pair(args, row, target, simd, guest, owner, out, name)
        checks, comparisons = row["correctness"], row["comparisons"]
        if any(result["status"] == "failed" for result in (*checks.values(), *comparisons.values())):
            row["status"] = "failed"
        elif any(result.get("within_1_5_target") is False for result in comparisons.values()):
            row["status"] = "mte-target-exceeded"
        elif (any(comparisons[name]["status"] == "measured" for name in external) and
              (not target.mte or comparisons["aot-disabled"]["status"] == "measured")):
            row["status"] = "measured"
        else:
            row["status"] = "comparison-open"
    except (OSError, ValueError, KeyError, TypeError) as error:
        row.update(status="failed", reason=str(error))
    write_json(out / "result.json", row)
    return row


def can_execute_natively(host, python_host):
    if host == python_host:
        return True
    # A 64-bit kernel may run the 32-bit ABI directly. The engines must still agree on their ELF host.
    if python_host == "linux-x86_64" and host == "linux-i686":
        return True
    return python_host in ("linux-arm", "linux-armhf", "linux-aarch64") and host in ("linux-arm", "linux-armhf")


def run(args, entries):
    args.work.mkdir(parents=True, exist_ok=True)
    require(not any(args.work.iterdir()), f"choose an empty --work directory: {args.work}")
    scratch = args.work / "tmp"
    scratch.mkdir()
    for key in ("TMPDIR", "TEMP", "TMP"):
        os.environ[key] = str(scratch)
    tempfile.tempdir = str(scratch)
    os.environ["XDG_CACHE_HOME"] = str(scratch / "cache")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    args.vm_target = args.vm_target.resolve()
    if args.vm_receipt:
        args.vm_receipt = args.vm_receipt.resolve()
    os.chdir(args.work)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    vm = verified_vm(args)
    require(vm_elf_host(args.vm) == args.host, "selected host differs from the actual VM ELF")
    python_host = vm_elf_host(Path("/proc/self/exe"))
    kernel = platform.uname()
    if args.environment != "user-qemu":
        require(can_execute_natively(args.host, python_host), "VM ABI differs from the running system; use --environment user-qemu for diagnostics")
        kernel_hosts = {"x86_64": "linux-x86_64", "i686": "linux-i686", "i386": "linux-i686",
                        "aarch64": "linux-aarch64", "arm64": "linux-aarch64"}
        kernel_host = kernel_hosts.get(kernel.machine, "linux-arm" if kernel.machine.startswith("armv") else None)
        require(can_execute_natively(args.host, kernel_host), "VM ABI differs from kernel architecture; use --environment user-qemu for diagnostics")
    affinity = sorted(os.sched_getaffinity(0))
    cpu = affinity[0] if args.cpu is None else args.cpu
    require(cpu in affinity, f"logical CPU {cpu} outside allowed affinity {affinity}")
    os.sched_setaffinity(0, {cpu})
    langs = sorted({entry[1] for entry in entries})
    args.sdk_receipts = {lang: sdk_identity(args.sdks[lang], lang) for lang in langs}
    reader = args.sdks[langs[0]] / "install"
    sys.path.insert(0, str(reader))
    from imports import inspect
    from artifacts import uleb
    args.references = references(args, args.work)
    modules = (HERE / "matrix.py", HERE / "workloads.py", HERE / "engines.py", HERE / "native-wasmtime-host.cpp",
               HERE.parent / "sysroot_suite.py",
               HERE.parent / "optional_isa_suite.py", HERE.parent / "wasmtime_reference/adapter.py")
    cpuinfo = Path("/proc/cpuinfo").read_text().split("\n\n")
    cpu_record = next((block for block in cpuinfo if re.search(rf"^processor\s*:\s*{cpu}$", block, re.M)), "")
    meta = {"format": 1, "command": sys.argv, "host": args.host, "environment": args.environment,
            "kernel": kernel._asdict(), "controller_elf_host": python_host, "logical_cpu": cpu,
            "cpuinfo": cpu_record, "samples_per_pair": args.samples,
            "vm": vm, "decoder": {"path": str(args.decoder), "sha256": digest(args.decoder)},
            "sdks": args.sdk_receipts, "references": args.references,
            "runner_sources": {str(p.relative_to(ROOT)): digest(p) for p in modules},
            "c_api_host_source_sha256": digest(HERE.parent / "wasmtime_reference/host.cpp"),
            "import_reader": str(reader), "inputs": {lang: public_inputs(lang) for lang in langs},
            "expected": {lang: expected(lang) for lang in langs}, "planned": len(entries)}
    if args.isolation_receipt:
        meta["isolation_receipt"] = {"path": str(args.isolation_receipt), "sha256": digest(args.isolation_receipt)}
    write_json(args.work / "inputs.json", meta)
    statuses, reference_statuses = Counter(), Counter()
    with (args.work / "results.jsonl").open("x") as results:
        for host, language, target, simd in entries:
            row = run_cell(args, host, language, target, simd, inspect, uleb)
            results.write(json.dumps(row) + "\n")
            results.flush()
            statuses[row["status"]] += 1
            for name, record in row["comparisons"].items():
                reference_statuses[name + "/" + record["status"]] += 1
            print(row["directory"], row["status"], flush=True)
    summary = {"planned": len(entries), "completed": sum(statuses.values()), "status": dict(statuses),
               "comparisons": dict(reference_statuses), "inputs_sha256": digest(args.work / "inputs.json"),
               "results_sha256": digest(args.work / "results.jsonl")}
    write_json(args.work / "summary.json", summary)
    if statuses["failed"] or statuses["mte-target-exceeded"]:
        return 1
    return 77 if statuses["comparison-open"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="write the selected plan as JSONL without building or running")
    parser.add_argument("--host", choices=HOSTS)
    parser.add_argument("--language", choices=LANGUAGES)
    parser.add_argument("--profile", choices=[t.name for t in TARGETS])
    parser.add_argument("--width", type=int, choices=(32, 64))
    for name in ("eh", "threads", "mte", "simd"):
        parser.add_argument("--" + name, choices=("on", "off"))
    for flag in ("cc-sdk", "cxx-sdk", "objc-sdk", "objcpp-sdk", "vm", "decoder", "wasmtime-host",
                 "wasmtime-cli", "wavm", "isolation-receipt", "work"):
        parser.add_argument("--" + flag, type=lambda path: Path(path).resolve())
    add_vm_identity_options(parser)
    parser.add_argument("--environment", choices=("native", "system-qemu", "user-qemu"), default="native",
                        help="system-qemu runs both engine ELFs inside the same booted system; user-qemu is diagnostic")
    parser.add_argument("--cpu", type=int, help="logical CPU shared by all engines, defaults to the first permitted CPU")
    parser.add_argument("--correctness-only", action="store_true")
    parser.add_argument("--samples", type=int, default=10, help="even number of alternating paired samples")
    parser.add_argument("--compile-timeout", type=int, default=240)
    parser.add_argument("--run-timeout", type=int, default=180)
    args = parser.parse_args()
    if not args.list:
        if args.vm is None or args.decoder is None:
            parser.error("execution requires --vm and --decoder")
        args.host = args.host or vm_elf_host(args.vm)
        if args.host not in HOSTS:
            parser.error("unrecognized VM ELF architecture")
    entries = list(selected(args))
    if not entries:
        parser.error("the supplied selectors describe no matrix cells")
    if args.list:
        for cell in entries:
            print(json.dumps(cell_key(*cell)))
        return 0
    if args.samples < 2 or args.samples % 2 or min(args.run_timeout, args.compile_timeout) <= 0:
        parser.error("choose an even sample count >= 2 and positive timeouts")
    args.sdks = {lang: getattr(args, LANGUAGES[lang][0]) for _, lang, _, _ in entries}
    if any(path is None for path in args.sdks.values()):
        parser.error("supply the installed binary SDK root for each selected language")
    if args.work is None:
        base = ROOT / ".tmp"
        base.mkdir(exist_ok=True)
        args.work = Path(tempfile.mkdtemp(prefix="cfamily-execution-", dir=base))
    print("Evidence directory", args.work, flush=True)
    return run(args, entries)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit(f"execution matrix: {exc}")
