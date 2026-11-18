"""Measure process-time slopes for two checked C workloads on native x86-64 and Wasm AOT.

Each timed invocation checks the full 32-bit result without guest IO. Slopes of
paired short/long runs reduce startup bias. Measurements still include process
startup variation and VM compilation. Native x86 does not emulate WasmMTE.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import time

from separate_compilation import Profile, cgroup_record, inspect, sha
from imports import Reader

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/memtag"


def exported_index(module, exported="benchmark"):
    data = module.read_bytes()
    if inspect(data):
        raise ValueError("unexpected guest import")
    reader = Reader(data)
    reader.take(8)
    while reader.position < len(reader.data):
        section = reader.byte()
        body = Reader(reader.take(reader.uint()))
        if section == 7:
            for _ in range(body.count()):
                name, kind, index = body.name(), body.byte(), body.uint()
                if name == exported and kind == 0:
                    return index
    raise ValueError("missing function export: " + exported)


def checksum(count):
    """Exponentiate the affine recurrence modulo 2^32, independently of the guest loop."""
    a, b, state = 1664525, 1013904223, 1
    while count:
        if count & 1:
            state = (a * state + b) & 0xffffffff
        a, b = (a * a) & 0xffffffff, (a * b + b) & 0xffffffff
        count >>= 1
    return state


def vtune_mapping(run, vtune, result_dir, label, function, analysis):
    """Resolve guest/native source when available, otherwise identify a sampled VM tag helper."""
    base = [vtune, "-report", "hotspots", "-result-dir", result_dir, "-format", "csv"]
    rc, _, table = run(label + "-lines", [*base, "-group-by", "function,source-file,source-line"], must=False)
    rows = list(csv.DictReader(table.splitlines(), delimiter="\t")) if rc == 0 else []
    exact = next((r for r in rows if r.get("Function") == function and r.get("Source File") == "stack_benchmark.c"
                  and r.get("Source Line", "").isdigit()), None)
    selected = exact or next((r for r in rows if "memtag" in r.get("Function", "").lower()
                              and r.get("Source Line", "").isdigit()), None)
    if not selected:
        return dict(mapped=False, host_helper_mapped=False, reason="no sampled source line for the workload or a VM tag helper")
    name = selected["Function"]
    metric = "Clockticks" if analysis == "uarch-exploration" else "Instructions Retired:Self"
    rc, _, table = run(label + "-assembly", [*base, "-source-object", "function=" + name,
        "-group-by", "address", "-column", "Assembly,Source Line," + metric], must=False)
    rows = list(csv.DictReader(table.splitlines(), delimiter="\t")) if rc == 0 else []
    positive = []
    for row in rows:
        if not row.get("Assembly") or not row.get("Source Line", "").isdigit():
            continue
        count = row.get(metric) or row.get(metric.removesuffix(":Self")) or ""
        count = count.replace(",", "")
        if count.isdigit() and int(count) > 0:
            positive.append(dict(line=int(row["Source Line"]), asm=row["Assembly"], event_count=int(count)))
    return dict(mapped=bool(exact and positive), host_helper_mapped=bool(exact is None and positive),
                function=name, source_file=selected["Source File"], metric=metric, sampled_instructions=len(positive),
                highest_count=max(positive, key=lambda r: r["event_count"], default=None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("toolchain", "sysroots", "plain-sysroots", "runtime", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    parser.add_argument("--native", type=Path, default=Path("/usr/bin/clang-22"))
    parser.add_argument("--vtune", type=Path, default=Path("/opt/intel/oneapi/vtune/latest/bin64/vtune"))
    args = parser.parse_args()
    work = args.output.resolve()
    if not work.is_relative_to(ROOT / ".tmp"):
        raise ValueError("use a new SDK .tmp output directory")
    group = cgroup_record()
    os.sched_setaffinity(0, {4})
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    toolchain, runtime = args.toolchain.resolve(), args.runtime.resolve()
    src = [FIXTURES / name for name in ("stack_benchmark.c", "stack_benchmark_mix.c")]
    native, wrapper, dump = args.native.resolve(), ROOT / "bin/wrc", toolchain / "bin/llvm-objdump"
    inputs = [Path(__file__), native, runtime, wrapper, dump, args.sysroots, args.plain_sysroots,
              toolchain / "bin/clang", *src, *sorted((ROOT / "install").glob("*.py"))]
    record = dict(timing_complete=False, hardware_complete=False, cgroup=group, cpu=4,
                  inputs={str(p): sha(p) for p in inputs}, commands=[], measurements={}, profiles=[],
                  scope="Process wall-time difference. x86-64 native without MTE versus Wasm32 AOT.")
    record["kernel"] = platform.release()
    record["cpu_model"] = next(line.partition(":")[2].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                               if line.startswith("model name"))
    record["perf_sysctls"] = {key: Path("/proc/sys/kernel", key).read_text().strip()
                              for key in ("perf_event_max_sample_rate", "perf_cpu_time_max_percent", "perf_event_paranoid")}
    report = work / "results.json"

    def save():
        report.write_text(json.dumps(record, indent=2) + "\n")

    def run(label, cmd, must=True, timeout=120):
        command = list(map(str, cmd))
        start = time.perf_counter_ns()
        try:
            p = subprocess.run(command, cwd=work, capture_output=True, timeout=timeout)
            elapsed = time.perf_counter_ns() - start
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            elapsed = time.perf_counter_ns() - start
            code, stdout, stderr = None, b"", str(exc).encode()
        (work / (label + ".stdout")).write_bytes(stdout)
        (work / (label + ".stderr")).write_bytes(stderr)
        record["commands"].append(dict(name=label, argv=command, exit=code, wall_ns=elapsed))
        save()
        if must and code != 0:
            raise RuntimeError(f"{label} failed: {stderr[-1500:]}")
        return code, elapsed, stdout.decode(errors="replace")

    save()
    exe = work / "native"
    run("build-native", [native, "-O3", "-g", "-fno-lto", *src, "-o", exe])
    run("native-assembly", ["/usr/bin/objdump", "-d", "-l", exe])
    modules = {}
    for compiled, receipt in (("mte", args.sysroots), ("plain", args.plain_sysroots)):
        module = work / (compiled + ".wasm")
        run("build-" + compiled, [wrapper, "--toolchain", toolchain, "--sysroots", receipt.resolve(),
            *(["--no-mte"] if compiled == "plain" else []), "--reactor", "--export", "benchmark",
            "-O3", "-g", *src, "-o", module])
        index = exported_index(module)
        modules[compiled] = (index, module)
        _, _, listing = run(compiled + "-disassembly", [dump, "-d", "-l", module])
        bounded = listing.split("<bounded_slot>:", 1)[1].split("\n\n", 1)[0]
        escaping = listing.split("<escaping_slot>:", 1)[1].split("\n\n", 1)[0]
        if "memtag." in bounded or ("memtag." in escaping) != (compiled == "mte"):
            raise RuntimeError("compiled stack tagging differs from the workload contract: " + compiled)
    record["artifact_sha256"] = {p.name: sha(p) for p in (exe, *(v[1] for v in modules.values()))}
    modes = ("native", "plain", "disabled", "enabled")

    def invocation(engine, escape, count):
        value = checksum(count)
        values = [str(n) for n in (escape, count, value & 65535, value >> 16)]
        if engine == "native":
            return [exe, *values]
        index, module = modules["plain" if engine == "plain" else "mte"]
        return [runtime, *Profile(32).uwvm_feature_flags(), "--runtime-aot", "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main",
                *(["--runtime-memtag-mode", "sync"] if engine == "enabled" else ["--runtime-disable-memtag"]),
                "--wasm-set-start-func", str(index), *values, "--run", module]

    for engine in modes:
        # Detect a silently skipped entry function before accepting any timing.
        cmd = invocation(engine, 0, 20)
        cmd[-2 if engine == "native" else -4] = str((checksum(20) & 65535) ^ 1)
        code, _, _ = run(engine + "-checksum-refused", cmd, must=False)
        if code is None or code == 0:
            raise RuntimeError("checksum control was not rejected by " + engine)
        for escape, case in enumerate(("bounded", "escaping")):
            label = engine + "-" + case
            _, empty, _ = run(label + "-empty", invocation(engine, escape, 0))
            count = 1 << 17
            while True:
                _, duration, _ = run(label + "-cal-" + str(count), invocation(engine, escape, count))
                if duration - empty >= 70_000_000 or count >= 1 << 26:
                    break
                count *= 2
            pairs = []
            for trial in range(7):
                lengths = (count, 3 * count) if trial % 2 == 0 else (3 * count, count)
                times = {n: run(f"{label}-{trial}-{n}", invocation(engine, escape, n))[1] for n in lengths}
                pairs.append((times[3 * count] - times[count]) / (2 * count))
            median = statistics.median(pairs)
            if median <= 0:
                raise RuntimeError("unresolved wall-time slope for " + label)
            record["measurements"][label] = dict(count=count, expected_checksum=checksum(count),
                 triple_checksum=checksum(3 * count), pair_ns=pairs, median_ns=median)
            save()
    record["timing_complete"] = True
    save()
    for engine in ("native", "enabled"):
        for escape, case in enumerate(("bounded", "escaping")):
            label = engine + "-" + case
            data = record["measurements"][label]
            repetitions = min(1 << 29, max(data["count"], int(700_000_000 / data["median_ns"])))
            for analysis, knobs in (("hotspots", ["sampling-mode=hw"]), ("uarch-exploration", ["pmu-collection-mode=detailed"])):
                prefix = label + "-" + analysis
                info = dict(engine=engine, workload=case, analysis=analysis, attempts=[], mapped=False)
                record["profiles"].append(info)
                for scale, extra in (("10us", ["sampling-interval=0.01"]), ("default", [])):
                    out = work / ("vtune-" + prefix + "-" + scale)
                    name = prefix + "-" + scale
                    cmd = [args.vtune, "-collect", analysis, *[arg for k in knobs + extra for arg in ("-knob", k)],
                        "-data-limit=80", "-no-analyze-system", "-return-app-exitcode", "-result-dir", out,
                        "-source-search-dir", FIXTURES, "--", *invocation(engine, escape, repetitions)]
                    rc, _, _ = run(name, cmd, must=False)
                    info["attempts"].append(dict(request=scale, exit=rc, stderr=name + ".stderr"))
                    if rc != 0:
                        continue
                    function = ("escaping_slot" if escape else "bounded_slot")
                    info.update(vtune_mapping(run, args.vtune, out, name, function, analysis))
                    if info["mapped"] or scale == "default":
                        break
                save()
    record["hardware_complete"] = all(x["mapped"] for x in record["profiles"])
    record["inputs_unchanged"] = all(sha(Path(p)) == h for p, h in record["inputs"].items())
    save()
    if not record["inputs_unchanged"]:
        raise RuntimeError("benchmark inputs changed during collection")
    print(json.dumps({k: v["median_ns"] for k, v in record["measurements"].items()}))
    print("VTune mappings complete:", record["hardware_complete"])


if __name__ == "__main__":
    main()
