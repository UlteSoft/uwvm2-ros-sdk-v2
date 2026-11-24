#!/usr/bin/env python3
"""Build or measure the C linear-access WasmMTE kernel in the offline qualification namespace."""

import argparse
import itertools
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import isolated
from sysroot_suite import digest, vm_elf_host

SOURCES = HERE / "mte_performance_sources"
SYSTEM_PYTHON = "/usr/bin/python3"
WORK = Path("/work")
VM = "/inputs/uwvm2-ros"
PROGRAMS = Path("/inputs/programs")
I686_LIBATOMIC = Path("/inputs/i686-lib/libatomic.so.1")
TRACER = "/inputs/strace"
PUBLISHED = Path("/qualification/mte-performance.json")
CELLS = tuple(itertools.product(("int", "aot"), (32, 64)))
MAX_ITERATIONS = 1 << 27
WASI_ALLOW = ("args_get", "args_sizes_get", "clock_time_get", "fd_fdstat_get", "fd_write", "proc_exit")
GRANTS = ("args", "monotonic-clock", "proc-exit", "stdio.metadata", "stdout.write", "stderr.write")
RESULT = re.compile(r"linear iterations=(\d+) checksum=(\d+) ns=(\d+) tag=(\d+)\n")


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def build(args):
    fixtures = WORK / "fixtures"
    fixtures.mkdir()
    gcc = "/usr/bin/gcc"
    native_argv = [gcc, "-std=c17", "-O3", str(SOURCES / "reference.c"), "-o", "/work/checksum"]
    subprocess.run(native_argv, check=True, timeout=120)
    known = json.loads(subprocess.check_output(["/work/checksum"], timeout=120))
    if known.keys() != {"0", *(str(1 << i) for i in range(28))}:
        raise ValueError("incomplete native checksum reference")
    save(fixtures / "checksums.json", known)

    driver = Path("/sdk/bin/wrc")
    source = WORK / "tools/linear-clock.c"
    # The absolute source, SDK and compilation directory also appear in the guest's DWARF.
    receipt = {"source_sha256": digest(source), "compiler_sha256": digest(driver),
               "reference_source_sha256": digest(SOURCES / "reference.c"), "reference_argv": native_argv,
               "checksums_sha256": digest(fixtures / "checksums.json"), "argv": [], "modules": {}}
    for bits, kind in itertools.product((32, 64), ("ordinary", "tagged")):
        if args.width and bits not in args.width:
            continue
        wasm = fixtures / f"linear-{bits}-{kind}.wasm"
        argv = [str(driver), "--target", f"wasm{bits}", "--core", "3.0", "--std", "c17", "-O3",
                "--reactor", "--export", "_start", "--no-threads", "--no-eh",
                "--mte" if kind == "tagged" else "--no-mte", "--build-receipt", str(source), "-o", str(wasm)]
        subprocess.run(argv, check=True, timeout=120)
        sidecar = wasm.with_suffix(".wasm.wros-build.json")
        details = json.loads(sidecar.read_bytes())
        sha = digest(wasm)
        if (details["artifact_sha256"] != sha or details["compiler_sha256"] != receipt["compiler_sha256"]
                or details["profile"]["address_bits"] != bits or details["profile"]["mte"] != (kind == "tagged")):
            raise ValueError(f"compiler receipt mismatch for {wasm.name}")
        receipt["argv"].append(argv)
        receipt["modules"][wasm.name] = {"sha256": sha, "receipt_sha256": digest(sidecar)}
    save(fixtures / "build-receipt.json", receipt)


def vm_command(bits, engine, mode, count):
    argv = [VM, "--runtime-" + engine, "--runtime-compile-threads", "0", "--debug-fault-action", "exit",
            "--log-color", "disable", "--wasm-feature-wasm3", "--wasm-feature-disable-threads",
            "--wasm-feature-disable-exceptions"]
    if bits == 64:
        argv += ["--wasm-feature-enable-memory64", "--wasm-feature-enable-table64"]
    if engine == "aot":
        argv += ["--runtime-llvm-jit-cache-path", "disable", "--runtime-llvm-jit-policy", "balanced"]
    if mode in ("ordinary", "disabled"):
        argv.append("--runtime-disable-memtag")
        if mode == "ordinary":
            argv.append("--wasm-feature-disable-memtag-extension")
    else:
        argv += ["--runtime-memtag-backend", mode, "--runtime-memtag-mode", "sync", "--runtime-memtag-action", "crash"]
    argv += ["--wasm-set-main-module-name", "main", "--wasip1-single-create", "main", "--wasip1-single-enable",
             "main", "--wasip1-single-hide-host-api", "main", "--wasip1-single-noinherit-system-environment", "main"]
    for name in (*WASI_ALLOW, "fd_close", "fd_seek"):
        interface = name + ("_wasm64" if bits == 64 else "")
        argv += ["--wasip1-single-interface", "main", interface, "allow" if name in WASI_ALLOW else "deny"]
    for grant in GRANTS:
        argv += ["--wasip1-single-grant", "main", grant]
    kind = "ordinary" if mode == "ordinary" else "tagged"
    return [*argv, "--run", str(PROGRAMS / f"linear-{bits}-{kind}.wasm"), str(count)]


def sample(bits, engine, mode, count, known, *, trace=False, env=None):
    argv = vm_command(bits, engine, mode, count)
    if trace:
        tracefile = WORK / f"{engine}-{bits}.strace"
        argv = [TRACER, "-f", "-qq", "-e", "trace=prctl,mmap,mprotect", "-o", str(tracefile), *argv]
    start = time.monotonic_ns()
    proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120, env=env)
    elapsed = time.monotonic_ns() - start
    match = RESULT.fullmatch(proc.stdout)
    if proc.returncode or not match:
        raise ValueError(f"{engine} wasm{bits} {mode} count={count} exited {proc.returncode}: "
                         f"{proc.stderr[-1500:] or proc.stdout[-256:]}")
    observed_count, checksum, ns, tag = map(int, match.groups())
    if (observed_count != count or checksum != known[str(count)] or (count and ns == 0)
            or bool(tag) != (mode in ("software", "hardware"))):
        raise ValueError(f"{engine} wasm{bits} {mode} count={count}: {proc.stdout.strip()}")
    result = {"guest_ns": ns, "elapsed_ns": elapsed, "checksum": checksum, "tag": tag}
    if trace:
        evidence = tracefile.read_text()
        success = r"\)\s+= (?:0|0x[0-9a-f]+)$"
        tagged_map = re.search(r"\b(?:mmap|mprotect)\(.*(?:PROT_MTE|\|0x20)\b.*" + success, evidence, re.M)
        sync = re.search(r"\bprctl\(PR_SET_TAGGED_ADDR_CTRL, [^)]*\bPR_MTE_TCF_SYNC\b[^)]*\)\s+= 0$",
                         evidence, re.M)
        if not tagged_map or not sync:
            raise ValueError(f"{engine} wasm{bits}: missing successful PROT_MTE mapping or synchronous tag control")
        result["trace_file"] = tracefile.name
        result["trace_sha256"] = digest(tracefile)
    return result


def quartiles(values):
    return statistics.quantiles(values, n=4, method="inclusive")


def measure_cell(args, index, engine, bits, known, env):
    modes = ("ordinary", "disabled", "software") + (("hardware",) if args.hardware else ())
    report = {"engine": engine, "wasm_bits": bits}
    if args.hardware:
        report["hardware_probe"] = sample(bits, engine, "hardware", 4096, known, trace=True)
    length = args.iterations
    if length is None:
        probe = 1 << (17 if args.emulated or engine == "int" else 21)
        calibration = sample(bits, engine, "software", probe, known, env=env)
        desired = probe * 320_000_000 // calibration["guest_ns"]
        length = min(MAX_ITERATIONS, 1 << max(14, desired.bit_length() - 1))
        report["calibration"] = {"iterations": probe, **calibration}
    sizes = (("long", length), ("short", length // 4), ("startup", 0))
    pairs = []
    for repeat in range(args.repeats):
        shift = (repeat + index) % len(modes)
        order = modes[shift:] + modes[:shift]
        if (repeat // len(modes)) % 2:
            order = order[::-1]
        shift = (repeat + index) % len(sizes)
        pair = {mode: {} for mode in modes}
        for label, count in sizes[shift:] + sizes[:shift]:
            for mode in order:
                pair[mode][label] = sample(bits, engine, mode, count, known, env=env)
        pairs.append(pair)
    ratios = {f"{mode}_over_{base}": quartiles([p[mode]["long"]["guest_ns"] / p[base]["long"]["guest_ns"]
                                               for p in pairs])
              for mode in modes[2:] for base in modes[:2]}
    slopes = {m: statistics.median((p[m]["long"]["guest_ns"] - p[m]["short"]["guest_ns"])
                                   / (length - length // 4) for p in pairs) for m in modes}
    report.update(iterations=length, checksum=known[str(length)], paired_ratios=ratios,
                  guest_ns_per_iteration={m: statistics.median(p[m]["long"]["guest_ns"] / length for p in pairs)
                                          for m in modes},
                  guest_growth_ns_per_iteration=slopes, pairs=pairs)
    print(f"{engine} wasm{bits}, {length} iterations, paired median software/ordinary "
          f"{ratios['software_over_ordinary'][1]:.4f}", flush=True)
    return report


def run(args, isolation):
    known_path = PROGRAMS / "checksums.json"
    checksums_sha = digest(known_path)
    receipt = json.loads((PROGRAMS / "build-receipt.json").read_bytes())
    published = json.loads(PUBLISHED.read_bytes())
    if digest(SOURCES / "linear-clock.c") != receipt["source_sha256"]:
        raise ValueError("kernel source differs from the build receipt")
    if "checksums_sha256" in receipt:
        if (checksums_sha != receipt["checksums_sha256"]
                or digest(SOURCES / "reference.c") != receipt["reference_source_sha256"]):
            raise ValueError("native checksum table or reference source differs from the build receipt")
    elif (digest(PROGRAMS / "build-receipt.json") != published["build_receipt_sha256"]
          or checksums_sha != "7f25ff66779dc15c0d4af9f94937239a9687e26020f39e4248cb426be4a6c7ac"):
        raise ValueError("unrecognized original build receipt or independent native checksum table")
    known = json.loads(known_path.read_bytes())
    cells = [(i, engine, bits) for i, (engine, bits) in enumerate(CELLS)
             if (not args.width or bits in args.width) and (not args.engine or engine in args.engine)]
    modules = {}
    for bits in sorted({bits for _, _, bits in cells}):
        for kind in ("ordinary", "tagged"):
            module = PROGRAMS / f"linear-{bits}-{kind}.wasm"
            modules[module.name] = digest(module)
            if modules[module.name] != receipt["modules"][module.name]["sha256"]:
                raise ValueError(f"program digest mismatch for {module.name}")
    host = vm_elf_host(VM)
    if not host:
        raise ValueError("expected an x86_64, i686, aarch64, arm or armhf Linux VM")
    if args.hardware and (host != "linux-aarch64" or os.uname().machine != "aarch64"):
        raise ValueError("hardware measurements require an AArch64 Linux host and VM")
    cpu = min(os.sched_getaffinity(0)) if args.cpu is None else args.cpu
    os.sched_setaffinity(0, {cpu})
    vm_sha = digest(Path(VM))
    report = {"host": host, "kernel": os.uname().release, "cpu": cpu, "system_qemu": args.emulated,
              "vm_sha256": vm_sha, "matches_published_vm": vm_sha == published["hosts"][host.removeprefix("linux-")]["program_sha256"],
              "matches_published_modules": all(receipt["modules"][name]["sha256"] == expected["sha256"]
                                               for name, expected in published["modules"].items()
                                               if name in receipt["modules"]),
              "build_receipt_sha256": digest(PROGRAMS / "build-receipt.json"), "checksums_sha256": checksums_sha,
              "module_sha256": modules,
              "repeats": args.repeats, "isolation": isolation, "measurements": []}
    env = None
    if args.phase == "x86-matrix" and host == "linux-i686" and args.i686_libatomic:
        if vm_elf_host(I686_LIBATOMIC) != host:
            raise ValueError("expected an i386 libatomic.so.1")
        report["i686_libatomic_sha256"] = digest(I686_LIBATOMIC)
        env = {**os.environ, "LD_LIBRARY_PATH": str(I686_LIBATOMIC.parent)}
    for index, engine, bits in cells:
        report["measurements"].append(measure_cell(args, index, engine, bits, known, env))
    save(WORK / "summary.json", report)


def launch(args, work, inputs):
    cfamily = Path("/checkout/src/qualification/cfamily")
    entry = cfamily / "mte_performance.py"
    readonly = [(Path(__file__).resolve(), entry),
                (HERE / "sysroot_suite.py", cfamily / "sysroot_suite.py"),
                (HERE.parent / "isolated.py", cfamily.parent / "isolated.py"),
                (SOURCES, cfamily / SOURCES.name), *inputs]
    for source, dest in readonly:
        source.resolve(strict=True)
    work.mkdir(parents=True, mode=0o700)
    namespace = argparse.Namespace(network="offline", vm=None, rust=None, xmake=None, xmake_data=None,
                                  command=[SYSTEM_PYTHON, "-I", "-B", str(entry),
                                           "--inside", *sys.argv[sys.argv.index(args.phase):]])
    return isolated.sandbox(namespace, work, readonly=readonly, strict_offline=True)


def x86_matrix(args, work, inputs):
    uname = os.uname()
    if (uname.sysname, uname.machine) != ("Linux", "x86_64"):
        raise ValueError("x86-matrix requires native x86_64 Linux with i686 execution support")
    vms = (("x86_64", args.vm_x86_64), ("i686", args.vm_i686))
    for abi, vm in vms:
        if vm_elf_host(vm) != "linux-" + abi or not os.access(vm, os.X_OK):
            raise ValueError(f"--vm-{abi} requires an executable Linux {abi} ELF")
    if args.i686_libatomic and vm_elf_host(args.i686_libatomic) != "linux-i686":
        raise ValueError("--i686-libatomic requires an i386 libatomic.so.1 ELF")
    for source, _ in inputs:
        if not source.is_file():
            raise ValueError(f"missing input file: {source}")
    allowed = os.sched_getaffinity(0)
    cpu = min(allowed) if args.cpu is None else args.cpu
    if cpu not in allowed:
        raise ValueError(f"CPU {cpu} is outside the permitted affinity")
    os.sched_setaffinity(0, {cpu})
    work.mkdir(parents=True, mode=0o700)
    cpuinfo = Path("/proc/cpuinfo").read_text().split("\n\n")
    selected = next((block for block in cpuinfo if re.match(rf"processor\s*:\s*{cpu}\n", block)), "")
    model = re.search(r"^model name\s*:\s*(.+)$", selected, re.M)
    matrix = {"host_machine": uname.machine, "kernel": uname.release, "cpu": cpu,
              "cpu_model": model[1] if model else None, "repeats": args.repeats, "hosts": {}}
    for abi, vm in vms:
        print(f"Measuring {abi} on CPU {cpu}", flush=True)
        mounts = [*inputs, (vm, Path(VM))]
        if abi == "i686" and args.i686_libatomic:
            mounts.append((args.i686_libatomic, I686_LIBATOMIC))
        status = launch(args, work / abi, mounts)
        if status:
            return status
        path = work / abi / "summary.json"
        raw = json.loads(path.read_bytes())
        cells = raw["measurements"]
        if (raw["host"] != "linux-" + abi or raw["cpu"] != cpu
                or tuple((m["engine"], m["wasm_bits"]) for m in cells) != CELLS):
            raise ValueError(f"unexpected host, CPU or cells in {path}")
        fixtures = {key: raw[key] for key in ("build_receipt_sha256", "checksums_sha256", "module_sha256")}
        if matrix.setdefault("fixtures", fixtures) != fixtures:
            raise ValueError("the two ABIs measured different fixtures")
        host = {"vm_sha256": raw["vm_sha256"], "matches_published_vm": raw["matches_published_vm"],
                "summary": str(path.relative_to(work)), "summary_sha256": digest(path),
                "measurements": [{k: m[k] for k in ("engine", "wasm_bits", "iterations", "paired_ratios")} for m in cells]}
        if "i686_libatomic_sha256" in raw:
            host["i686_libatomic_sha256"] = raw["i686_libatomic_sha256"]
        matrix["hosts"][abi] = host
    pending = work / "matrix.json.tmp"
    save(pending, matrix)
    pending.replace(work / "matrix.json")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--work", type=Path, required=True, help="new directory below the SDK checkout's .tmp")
    phases = parser.add_subparsers(dest="phase", required=True)
    compiler = phases.add_parser("build", parents=[common])
    compiler.add_argument("--cc-sdk", type=Path, required=True, help="installed C prefix containing bin/wrc")
    runner = phases.add_parser("run", parents=[common])
    runner.add_argument("--vm", type=Path, required=True)
    runner.add_argument("--engine", choices=("int", "aot"), action="append", help="repeatable, default both")
    runner.add_argument("--emulated", action="store_true", help="use the system-QEMU calibration length")
    runner.add_argument("--hardware", action="store_true", help="add explicit AArch64 synchronous hardware MTE")
    runner.add_argument("--strace", type=Path, default=Path("/usr/bin/strace"), help="tracer for --hardware")
    matrix = phases.add_parser("x86-matrix", parents=[common], help="measure x86_64 and i686 software MTE on one CPU")
    matrix.add_argument("--vm-x86_64", type=Path, required=True)
    matrix.add_argument("--vm-i686", type=Path, required=True)
    matrix.add_argument("--i686-libatomic", type=Path, help="local i386 libatomic.so.1 for the i686 VM")
    matrix.set_defaults(width=None, engine=None, hardware=False, emulated=False)
    for phase in (compiler, runner):
        phase.add_argument("--width", choices=(32, 64), type=int, action="append", help="repeatable, default both")
    for phase in (runner, matrix):
        phase.add_argument("--programs", type=Path, required=True, help="fixtures directory made by build")
        phase.add_argument("--iterations", type=int, help="fixed power of two, 16384 through 134217728")
        phase.add_argument("--repeats", type=int, default=5)
        phase.add_argument("--cpu", type=int, help="logical CPU, default first allowed CPU")
    args = parser.parse_args()
    if args.phase != "build" and (args.repeats < 2 or args.iterations is not None and (
            not 16384 <= args.iterations <= MAX_ITERATIONS or args.iterations & (args.iterations - 1))):
        parser.error("use at least two repeats and a power-of-two length from 16384 through 134217728")
    if not (args.scope or args.inside):
        return isolated.scope([SYSTEM_PYTHON, "-I", "-B", str(Path(__file__).resolve()), "--scope", *sys.argv[1:]])
    if sys.version_info < (3, 11):
        parser.error(f"qualification requires Python 3.11 or newer (running {sys.version.split()[0]})")
    if args.inside:
        isolation = isolated.verify_offline_namespace()
        if args.phase == "build":
            build(args)
        else:
            run(args, isolation)
        return 0

    # Only the launcher crosses the sandbox boundary. Compiler/VM arguments use mounted paths.
    isolated.cgroup_info()
    project = isolated.ROOT
    work = args.work.resolve()
    if project / ".tmp" not in work.parents:
        parser.error("--work must be a new directory below the SDK checkout's .tmp")
    nearest = next(p for p in (work, *work.parents) if p.exists())
    if nearest.stat().st_dev != project.stat().st_dev:
        parser.error("--work must reside on the checkout's project filesystem")
    if args.phase == "build":
        return launch(args, work, [(args.cc_sdk, Path("/sdk")), (SOURCES, WORK / "tools")])
    inputs = [(project / "document/qualification/cfamily-mte-performance.json", PUBLISHED)]
    if args.phase == "x86-matrix":
        names = ["build-receipt.json", "checksums.json", *(f"linear-{bits}-{kind}.wasm"
                 for bits, kind in itertools.product((32, 64), ("ordinary", "tagged")))]
        inputs.extend((args.programs / name, PROGRAMS / name) for name in names)
        return x86_matrix(args, work, inputs)
    inputs += [(args.vm, Path(VM)), (args.programs, PROGRAMS)]
    if args.hardware:
        inputs.append((args.strace, Path(TRACER)))
    return launch(args, work, inputs)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
