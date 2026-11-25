#!/usr/bin/env python3
"""Exercise independently linked wrc reactors importing the same env.memory."""
import argparse
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent)]
from sysroot_suite import SHARED_MEMORY_PAGES, capture, digest
import isolated

BASE = (SHARED_MEMORY_PAGES - 1) * 65536
CASES = ("raw-offset", "pointer-call", "pointer-slot", "zero-fill", "zero-pointer", "zero-allocation")
PAIRS = tuple("-".join(pair) for pair in itertools.product(("plain", "mte"), repeat=2))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(args, directory, bits, pairs):
    from artifacts import sections
    from imports import inspect

    def compiled(command, name):
        result = capture(command, directory, name, 240)
        require(result.get("returncode") == 0, f"build failed: {directory / (name + '.err')}")
        return result

    builds = {}
    for side, letter in enumerate("ab"):
        for mode in sorted({pair.split("-")[side] for pair in pairs}):
            name = f"{letter}-{mode}"
            wasm = directory / (name + ".wasm")
            result = compiled([args.cc_sdk / "bin/wrc", "--target", f"wasm{bits}", "--core", "3.0",
                               "--std", "c17", "-O2", "--no-eh", "--threads", "--shared-memory-pages",
                               str(SHARED_MEMORY_PAGES), "--reactor", "--mte" if mode == "mte" else "--no-mte",
                               "--build-receipt", "-D", f"ABI_BASE={BASE}", "-D", f"ABI_SIDE={side}",
                               "-D", f"ABI_MTE={int(mode == 'mte')}", HERE / "endpoint.c", "-o", wasm], name)
            receipt = wasm.with_suffix(".wasm.wros-build.json")
            record = json.loads(receipt.read_bytes())
            profile = record["profile"]
            sha = digest(wasm)
            require(record["artifact_sha256"] == sha and record["language"] == "c"
                    and profile["address_bits"] == bits and profile["mte"] == (mode == "mte")
                    and profile["threads"] and profile["exceptions"] == "noeh", f"{name}: wrc receipt differs")
            data = wasm.read_bytes()
            widths = []
            imports = inspect(data, memory_limits=True, memory_types=widths)
            require(widths == [bits] and len(imports) == 1 and imports[0]["kind"] == 2
                    and (imports[0]["module"], imports[0]["name"]) == ("env", "memory"),
                    f"{name}: expected one shared memory import")
            flags, minimum, maximum = imports[0]["limits"]
            require(flags == (7 if bits == 64 else 3) and maximum == SHARED_MEMORY_PAGES
                    and 0 < minimum < maximum, f"{name}: reserved ABI page overlaps the linker's footprint")
            for start, _, _, body in sections(data):
                if data[start] == 11:
                    require(body.count() == 0, f"{name}: endpoint introduced a data segment")
            builds[name] = {**result, "sha256": sha, "receipt_sha256": digest(receipt), "imports": imports,
                            "compiler_sha256": record["compiler_sha256"], "sysroot_sha256": record["sysroot_sha256"]}

    memory_type = "i64 " if bits == 64 else ""
    pages = SHARED_MEMORY_PAGES
    owner = f'(module (memory (export "memory") {memory_type}{pages} {pages} shared))'
    adapter = (HERE / "adapter.wat.in").read_text().replace("PTR", f"i{bits}")
    for name, source in (("owner", owner), ("adapter", adapter)):
        wat, wasm = directory / (name + ".wat"), directory / (name + ".wasm")
        wat.write_text(source)
        command = [args.wat2wasm, "--enable-memory64", "--enable-threads", wat, "-o", wasm]
        builds[name] = {**compiled(command, name), "sha256": digest(wasm)}

    # The UWVM start selector uses local function indices. Resolve the exported
    # case names from the exact adapter binary instead of relying on source order.
    data = (directory / "adapter.wasm").read_bytes()
    imported = len(inspect(data))
    entries = {}
    for start, _, _, body in sections(data):
        if data[start] == 7:
            for _ in range(body.count()):
                name, kind, index = body.name(), body.byte(), body.uint()
                require(kind == 0 and index >= imported, f"unexpected adapter export {name}")
                entries[name] = index - imported
    require(set(entries) == set(CASES), "adapter case inventory differs")
    (directory / "build.json").write_text(json.dumps(builds, indent=2) + "\n")
    return entries


def cases(bits, pair, policy):
    left, right = pair.split("-")
    tag = 0xb if bits == 32 else 0xab
    shift = 28 if bits == 32 else 56
    masks = [(tag << shift) if policy == "on" and profile == "mte" else 0 for profile in (left, right)]
    a, b = BASE + 64, BASE + 128
    yield "raw-offset", [], None
    yield "pointer-call", [a | masks[0], b | masks[1]], None
    yield "pointer-slot", [a | masks[0], b | masks[1]], None
    yield "zero-fill", [a, a | masks[0]], None
    if left == "mte":
        for case, expected, pointer, granule, logical, allocation in (
                ("zero-pointer", a | masks[0], a + 3, a, 0, tag),
                ("zero-allocation", BASE | masks[0], BASE | masks[0], BASE, tag, 0)):
            for store in (0, 1):
                fault = {"Pointer": pointer, "Granule": granule, "Pointer tag": logical,
                         "Allocation tag": allocation, "Memory index": 0} if masks[0] else None
                yield case, [expected, store], fault


def exercise(args, directory, entries, bits, pair, engine, policy, case, params, fault):
    left, right = pair.split("-")
    name = case
    if case in ("zero-pointer", "zero-allocation"):
        name += "-write" if params[-1] else "-read"
    out = directory / pair / engine / policy
    out.mkdir(parents=True, exist_ok=True)
    cmd = [args.vm, "--runtime-" + engine, "--runtime-compile-threads", "0", "--debug-fault-action", "exit",
           "--log-color", "disable", "--wasm-feature-wasm3", "--wasm-feature-enable-threads"]
    if bits == 64:
        cmd += ["--wasm-feature-enable-memory64", "--wasm-feature-enable-table64"]
    if engine == "aot":
        cmd += ["--runtime-llvm-jit-cache-path", "disable"]
    if policy == "on":
        cmd += ["--runtime-memtag-backend", "software", "--runtime-memtag-mode", "sync", "--runtime-memtag-action", "crash"]
    else:
        cmd.append("--runtime-disable-memtag")
    for module, alias in (("owner", "env"), ("a-" + left, "a"), ("b-" + right, "b")):
        cmd += ["--wasm-preload-library", directory / (module + ".wasm"), alias]
    cmd += ["--wasm-set-start-func", str(entries[case]), *map(str, params), "--run", directory / "adapter.wasm"]
    result = capture(cmd, out, name, 90)
    log = (out / (name + ".err")).read_text(errors="replace").splitlines()
    expected = 122 if fault else 0
    passed = result.get("returncode") == expected and (out / (name + ".out")).stat().st_size == 0
    if fault:
        backend = "LLVM" if engine == "aot" else "interpreter"
        lines = ["uwvm: [crash] memory-protection", "  Reason: memory tag mismatch",
                 "  Exit status: 122", "  Backend: " + backend, *(f"  {k}: {v}" for k, v in fault.items())]
        passed = passed and all(log.count(line) == 1 for line in lines)
    else:
        passed = passed and not any("[crash]" in line or "[fatal]" in line for line in log)
    return {**result, "width": bits, "pair": pair, "engine": engine, "policy": policy, "case": name,
            "expected_exit": expected, "expected_fault": fault, "passed": passed,
            "log_prefix": str((out / name).relative_to(args.work))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("cc-sdk", "vm", "work"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--wat2wasm", type=Path, default=Path("/usr/bin/wat2wasm"))
    parser.add_argument("--width", choices=(32, 64), type=int)
    parser.add_argument("--pair", choices=PAIRS)
    parser.add_argument("--engine", choices=("int", "aot"))
    parser.add_argument("--policy", choices=("on", "off"))
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--isolate", action="store_true", help="launch in the SDK's strict offline qualification harness")
    parser.add_argument("--scope", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    for key in ("cc_sdk", "vm", "work", "wat2wasm"):
        setattr(args, key, getattr(args, key).resolve())
    if args.isolate:
        if not args.scope:
            return isolated.scope([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--scope", *sys.argv[1:]])
        require(isolated.ROOT / ".tmp" in args.work.parents, "--isolate work must be below the SDK checkout's .tmp")
        args.work.mkdir(parents=True, exist_ok=True)
        qualification = Path("/checkout/src/qualification")
        command = ["/usr/bin/python3", "-I", "-B", str(qualification / "cfamily/shared_memory_abi/run.py"),
                   "--inside", "--cc-sdk", "/sdk", "--vm", "/opt/tools/bin/uwvm2-ros", "--wat2wasm", "/tools/wat2wasm",
                   "--work", "/work/results"]
        for name in ("width", "pair", "engine", "policy", "case"):
            if getattr(args, name) is not None:
                command.extend(["--" + name, str(getattr(args, name))])
        namespace = argparse.Namespace(command=command, network="offline", vm=args.vm, xmake=None, xmake_data=None, rust=None)
        return isolated.sandbox(namespace, args.work, readonly=[(HERE.parent.parent, qualification),
                                (args.cc_sdk, "/sdk"), (args.wat2wasm, "/tools/wat2wasm")], strict_offline=True)

    isolation = isolated.verify_offline_namespace() if args.inside else None
    if args.work.exists() and any(args.work.iterdir()):
        parser.error("select an empty output directory")
    pairs = [args.pair] if args.pair else PAIRS
    if args.pair and args.pair.startswith("plain-") and args.case in ("zero-pointer", "zero-allocation"):
        parser.error("these cases require an MTE-producing first endpoint")
    args.work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.cc_sdk / "install"))
    inputs = {"vm_sha256": digest(args.vm), "wrc_sha256": digest(args.cc_sdk / "bin/wrc"),
              "wat2wasm_sha256": digest(args.wat2wasm), "isolation": isolation,
              "sources": {path.name: digest(path) for path in (HERE / "endpoint.c", HERE / "adapter.wat.in", Path(__file__))}}
    (args.work / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    total = passed = 0
    with (args.work / "results.jsonl").open("x") as output:
        for bits in [args.width] if args.width else (32, 64):
            directory = args.work / f"wasm{bits}"
            directory.mkdir()
            entries = build(args, directory, bits, pairs)
            for pair, engine, policy in itertools.product(pairs, [args.engine] if args.engine else ("int", "aot"),
                                                        [args.policy] if args.policy else ("on", "off")):
                for case, params, fault in cases(bits, pair, policy):
                    if args.case and case != args.case:
                        continue
                    row = exercise(args, directory, entries, bits, pair, engine, policy, case, params, fault)
                    print(json.dumps(row), file=output, flush=True)
                    print(bits, pair, engine, policy, row["case"], "PASS" if row["passed"] else "FAIL", flush=True)
                    total += 1
                    passed += row["passed"]
    (args.work / "summary.json").write_text(json.dumps({"total": total, "passed": passed}) + "\n")
    return int(not total or passed != total)


if __name__ == "__main__":
    raise SystemExit(main())
