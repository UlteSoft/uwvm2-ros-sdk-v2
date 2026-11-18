"""Compare the numeric C# component import against an out-of-line native integer function."""
import argparse
import csv
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import time

from separate_compilation import cgroup_record, Profile, sha
from artifacts import sections
from imports import inspect

FIXTURES = Path(__file__).resolve().with_name("csharp")


def mapping(run, vtune, result, label, target, analysis):
    """Find sampled statements and retained instructions for the guest or its VM dispatcher."""
    base = [vtune, "-report", "hotspots", "-r", result, "-format", "csv", "-csv-delimiter", "tab"]
    status, _, table = run(label + "-lines", [*base, "-group-by", "function,source-file,source-line"], must=False)
    rows = list(csv.DictReader(table.splitlines(), delimiter="\t")) if status == 0 else []
    target_rows = [r for r in rows if r.get("Function") == target and r.get("Source Line", "").isdigit()
                   and int(r["Source Line"]) > 0]
    if not target_rows:
        return dict(mapped=False, reason="no samples attributable to the selected function and source")
    metric = "Clockticks" if analysis == "uarch-exploration" else "Instructions Retired:Self"
    status, _, table = run(label + "-assembly", [*base, "-source-object", "function=" + target,
                           "-group-by", "address", "-column", "Assembly,Source Line," + metric], must=False)
    asm = list(csv.DictReader(table.splitlines(), delimiter="\t")) if status == 0 else []
    evidence = []
    for row in asm:
        raw = (row.get(metric) or row.get(metric.removesuffix(":Self")) or "").replace(",", "")
        if row.get("Assembly") and row.get("Source Line", "").isdecimal() and raw.isdecimal() and int(raw) > 0:
            evidence.append(dict(line=int(row["Source Line"]), asm=row["Assembly"], events=int(raw)))
    return dict(mapped=bool(evidence), function=target,
                sampled_source=[{key: row[key] for key in ("Source File", "Source Line")} for row in target_rows[:12]],
                peak=max(evidence, key=lambda row: row["events"], default=None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("module", "vm", "toolchain", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--native", type=Path, default=Path("/usr/bin/clang-22"))
    parser.add_argument("--vtune", type=Path, default=Path("/opt/intel/oneapi/vtune/latest/bin64/vtune"))
    opts = parser.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {4})
    module = opts.module.resolve()
    vm = opts.vm.resolve()
    tool = opts.toolchain.resolve() / "bin"
    out = opts.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    native_c = FIXTURES / "numeric-native.c"
    calls = FIXTURES / "numeric-calls.c"
    exe = out / "native"
    caller = out / "caller.wasm"
    tools = [vm, module, calls, native_c, opts.native.resolve(), opts.vtune.resolve(), tool / "clang"]
    report = dict(complete=False, cgroup=group, measurements={}, profiles=[], commands=[],
                  inputs={str(p): sha(p) for p in tools})
    env = dict(os.environ, TMPDIR=str(out))

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, must=True):
        command = list(map(str, argv))
        begin = time.monotonic_ns()
        proc = subprocess.run(command, cwd=out, env=env, capture_output=True, timeout=180)
        elapsed = time.monotonic_ns() - begin
        (out / (name + ".stdout")).write_bytes(proc.stdout)
        (out / (name + ".stderr")).write_bytes(proc.stderr)
        report["commands"].append(dict(name=name, argv=command, exit=proc.returncode, elapsed_ns=elapsed))
        save()
        if must and proc.returncode:
            raise ValueError(name + ": " + proc.stderr.decode(errors="replace")[-1200:])
        return proc.returncode, elapsed, proc.stdout.decode(errors="replace")

    run("native-build", [opts.native, "-O3", "-g", "-fno-lto", calls, native_c, "-o", exe])
    run("native-asm", ["/usr/bin/objdump", "-dl", exe])
    run("guest-caller", [tool / "clang", "--no-default-config", "--target=wasm32-wasip1", "-O3", "-g",
                         "-ffreestanding", "-nostdlib", calls, "-Wl,--no-entry,--export=check", "-o", caller])
    run("guest-asm", [tool / "llvm-objdump", "-dl", module])
    data = caller.read_bytes()
    imported = inspect(data)
    if len(imported) != 1 or (imported[0]["module"], imported[0]["name"]) != ("component", "evaluate") or inspect(module.read_bytes()):
        raise ValueError("unexpected imports in the numeric kernel or its timing harness")
    defined_index = None
    for start, _, _, body in sections(data):
        if data[start] == 7:
            for _ in range(body.count()):
                name, kind, index = body.name(), body.byte(), body.uint()
                if name == "check" and kind == 0 and index >= len(imported):
                    defined_index = index - len(imported)
    if defined_index is None:
        raise ValueError("missing timing harness entry")

    def invoke(engine, iterations):
        if engine == "native":
            return [exe, str(iterations)]
        return [vm, *Profile().uwvm_feature_flags(), "--runtime-aot", "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                "--wasm-preload-library", module, "component", "--wasm-set-start-func", str(defined_index),
                str(iterations), "--run", caller]

    count = 1 << 24
    for engine in ("native", "aot"):
        for warm in range(2):
            run(f"{engine}-warm-{warm}", invoke(engine, 10000))
        pairs = []
        for trial in range(7):
            lengths = (count, 3 * count) if trial % 2 == 0 else (3 * count, count)
            times = {n: run(f"{engine}-{trial}-{n}", invoke(engine, n))[1] for n in lengths}
            pairs.append((times[3 * count] - times[count]) / (2 * count))
        median = statistics.median(pairs)
        if median <= 0:
            raise ValueError("nonpositive paired slope")
        report["measurements"][engine] = dict(paired_ns=pairs, median_ns=median, count=count)
    report["ratio"] = report["measurements"]["aot"]["median_ns"] / report["measurements"]["native"]["median_ns"]

    for engine in ("native", "aot"):
        for analysis, setting in (("hotspots", "sampling-mode=hw"), ("uarch-exploration", "pmu-collection-mode=detailed")):
            record = dict(engine=engine, analysis=analysis, mapped=False, attempts=[])
            report["profiles"].append(record)
            for interval, extra in (("10us", ["-knob", "sampling-interval=0.01"]), ("default", [])):
                label = engine + "-" + analysis + "-" + interval
                result = out / ("vtune-" + label)
                status, _, _ = run(label, [opts.vtune, "-collect", analysis, "-knob", setting, *extra,
                                           "-result-dir", result, "--", *invoke(engine, 1 << 27)], must=False)
                record["attempts"].append(dict(interval=interval, exit=status))
                if status:
                    continue
                function = "evaluate" if engine == "native" else "uwvm2::runtime::lib::details::llvm_jit_call_raw_from_generated_wasm"
                record.update(mapping(run, opts.vtune, result, label, function, analysis))
                rc, _, table = run(label + "-functions", [opts.vtune, "-report", "hotspots", "-r", result,
                                   "-format", "csv", "-csv-delimiter", "tab", "-limit", "12"], must=False)
                if rc == 0:
                    record["sampled_functions"] = [row.get("Function") for row in csv.DictReader(table.splitlines(), delimiter="\t")]
                break
            save()
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
