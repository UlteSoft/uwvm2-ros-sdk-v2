#!/usr/bin/env python3
"""Qualify the installed C-family frontends' optional instruction lowering on INT and AOT."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import secrets
import struct
import sys

from sysroot_suite import (SHARED_MEMORY_PAGES, Target, add_vm_identity_options, capture, digest,
                           runtime_args, verified_vm)

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "optional_isa_fixtures"
LANGUAGES = {"c": ("cc_sdk", "wrc", ".c", "c17"), "cpp": ("cxx_sdk", "wrcc", ".cpp", "c++20"),
             "objc": ("objc_sdk", "wroc", ".m", "c17"), "objcpp": ("objcpp_sdk", "wrocxx", ".mm", "c++20")}
TARGETS = [Target(*axes) for axes in itertools.product((32, 64), (False, True), (False, True), (False, True))]
FIXED = (0, 1, 0x80000000, 0xffffffff)
MASK = (1 << 32) - 1
ISA_KEYS = {"simd_total", "simd_arithmetic", "relaxed_simd_total", "memory_copy", "memory_fill",
            "other_bulk", "scalar_loads", "scalar_stores", "calls"}
PROFILE_KEYS = {"bodies", "memtag_total", "threads_total", "shared_memories", "thread_spawn_imports", "eh_total", "tags"}


def oracle(seeds):
    data = bytearray()
    for seed in seeds:
        lanes = []
        for i in range(64):
            left = (seed + 17 + i * 0x9e3779b9) & MASK
            right = ((seed ^ 0x7f4a7c15) - i * 0x85ebca6b) & MASK
            lanes.append(((left + right) ^ (left * 33)) & MASK)
        data.extend(struct.pack("<66I", seed, *lanes, sum(lanes) & MASK))
        memory = bytearray()
        state = seed
        for _ in range(64):
            state = (state * 1664525 + 1013904223) & MASK
            memory.append(state >> 24)
        delta, count = 1 + (seed & 7), 24 + ((seed >> 8) & 7)
        length = 2 + ((seed >> 12) & 15)
        memory[4:4 + length] = bytes([seed & 255]) * length
        data.extend(memory)
        for to, src, n in ((8 + delta, 8, count), (8, 8 + delta, count), (1, 64, 0)):
            memory[to:to + n] = memory[src:src + n]
            data.extend(memory)
    return bytes(data)


def memory_owner(out, target, imports, uleb):
    memories = [item for item in imports if item["kind"] == 2]
    if len(memories) != 1:
        raise ValueError("expected one imported shared memory")
    memory, = memories
    flags, low, high = memory["limits"]
    if ((memory["module"], memory["name"]) != ("env", "memory") or flags != (7 if target.bits == 64 else 3)
            or not 0 < low <= high == SHARED_MEMORY_PAGES):
        raise ValueError("shared memory owner type differs from the selected profile")
    # The imported memory needs an owner instance. This module contains only
    # the memory and export sections. Every executed instruction comes from
    # the application, its guest libraries, or the guest linker.
    mem = b"\x01" + uleb(flags) + uleb(low) + uleb(high)
    export = b"\x01\x06memory\x02\x00"
    path = out / "owner.wasm"
    path.write_bytes(b"\0asm\x01\0\0\0\x05" + uleb(len(mem)) + mem + b"\x07" + uleb(len(export)) + export)
    return path


def fields(line, keys):
    values = {key: int(value) for key, value in re.findall(r" (\w+)=(\d+)(?= |$)", line) if key in keys}
    if values.keys() != keys:
        raise ValueError("decoder missing fields: " + ", ".join(sorted(keys - values.keys())))
    return values


def decode_log(path):
    lines = path.read_text().splitlines()
    if not lines or not lines[0].startswith("MODULE "):
        raise ValueError("missing sequential module decode")
    counts = fields(lines[0], ISA_KEYS | PROFILE_KEYS)
    functions = {}
    for line in lines[1:]:
        if not line.startswith("FUNCTION "):
            continue
        parts, quoted = line.rsplit(" name=", 1)
        # wasmparser debug strings are quoted. The package's C symbols and
        # export names are ASCII. Preserve a foreign name's escaped spelling.
        name = quoted[1:-1]
        calls = parts.split(" direct_calls=")[1]
        index = int(parts.split(" ", 2)[1])
        functions[index] = {"name": name, **fields(parts, ISA_KEYS),
                            "direct_calls": [int(i) for i in calls.split(",") if i]}
    if not functions:
        raise ValueError("no --functions output from decoder")
    return counts, functions


def instruction_evidence(target, simd, bulk, counts, functions, widths):
    errors = []
    if widths != [target.bits] or counts["shared_memories"] != int(target.threads):
        errors.append("memory type does not match profile")
    if not target.mte and counts["memtag_total"]:
        errors.append("MTE instructions with MTE disabled")
    if target.mte and not counts["memtag_total"]:
        errors.append("MTE workload has no MTE instructions")
    if not target.eh and (counts["tags"] or counts["eh_total"]):
        errors.append("exception handling with EH disabled")
    if not target.threads and (counts["threads_total"] or counts["thread_spawn_imports"]):
        errors.append("thread instructions or imports with threads disabled")
    if target.threads and not counts["threads_total"]:
        errors.append("shared workload lacks thread instructions")
    by_name = {f["name"]: f for f in functions.values()}
    vector, move, fill = (by_name.get(name) for name in ("isa_vector", "isa_move", "isa_fill"))
    if not all((vector, move, fill)):
        raise ValueError("decoder did not identify all three exported workload functions")
    if simd and not vector["simd_arithmetic"]:
        errors.append("vector kernel lacks packed arithmetic")
    if not simd and (not vector["scalar_loads"] or not vector["scalar_stores"]):
        errors.append("scalar vector kernel lacks ordinary loads or stores")
    if bulk and not move["memory_copy"]:
        errors.append("memmove kernel lacks memory.copy")
    if bulk and not fill["memory_fill"]:
        errors.append("memset kernel lacks memory.fill")
    if not bulk:
        for caller, target_name in ((move, "memmove"), (fill, "memset")):
            # When LLVM emits a libcall, require its direct callee in this very
            # file to implement the operation with scalar loads/stores.
            candidates = [caller] + [functions[i] for i in caller["direct_calls"]
                                     if i in functions and functions[i]["name"] == target_name]
            if not any(f["scalar_stores"] and (target_name == "memset" or f["scalar_loads"])
                       for f in candidates):
                errors.append(f"{target_name} path lacks ordinary memory access")
    banned = ([] if simd else ["simd_total", "relaxed_simd_total"]) + ([] if bulk else ["memory_copy", "memory_fill"])
    violations = {key: counts[key] for key in banned if counts[key]}
    if violations:
        errors.append("disabled instructions in final module")
    offenders = [{"index": i, "name": f["name"], **{key: f[key] for key in violations if f[key]}}
                 for i, f in functions.items() if any(f[key] for key in violations)]
    return {"errors": errors, "whole_module": counts, "kernels": {f["name"]: f for f in (vector, move, fill)},
            "disabled_in_final_module": violations, "offending_functions": offenders}


def run_cell(args, language, target, simd, bulk, seeds, expected, inspect, uleb):
    sdk_option, command, extension, standard = LANGUAGES[language]
    sdk = getattr(args, sdk_option)
    out = args.work / language / target.name / f"simd-{int(simd)}-bulk-{int(bulk)}"
    out.mkdir(parents=True)
    wasm, source = out / "guest.wasm", FIXTURES / ("probe" + extension)
    row = {"language": language, "profile": target.name, "simd": simd, "bulk": bulk, "runs": {},
           "directory": str(out.relative_to(args.work))}
    def finish(status):
        row["status"] = status
        (out / "result.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    try:
        command = [sdk / "bin" / command, "--target", f"wasm{target.bits}", "--core", "3.0", "-O3", "-g",
                   "--std", standard, "--threads" if target.threads else "--no-threads",
                   "--eh" if target.eh else "--no-eh", "--mte" if target.mte else "--no-mte",
                   "-msimd128" if simd else "-mno-simd128", "-mbulk-memory-opt" if bulk else "-mno-bulk-memory-opt",
                   "--build-receipt", "--export", "isa_vector", "--export", "isa_move", "--export", "isa_fill",
                   "-D", "ISA_SEEDS=" + ",".join(f"0x{x:08x}u" for x in seeds)]
        if target.threads:
            command += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)]
        row["compile"] = capture([*command, source, "-o", wasm], out, "compile", args.compile_timeout)
        if row["compile"].get("returncode") != 0:
            return finish("compile-failed")
        receipt_path = Path(str(wasm) + ".wros-build.json")
        receipt = json.loads(receipt_path.read_bytes())
        row["wasm_sha256"] = digest(wasm)
        row["receipt_sha256"] = digest(receipt_path)
        profile = receipt["profile"]
        expected_profile = {"address_bits": target.bits, "wasm_version": "3.0", "threads": target.threads,
                            "mte": target.mte, "exceptions": "eh" if target.eh else "noeh"}
        isa = receipt["optional_isa"]
        if (receipt["artifact_sha256"] != row["wasm_sha256"] or receipt["language"] != language
                or any(profile.get(k) != v for k, v in expected_profile.items())
                or any(isa.get(k) is not v for k, v in (("simd128", simd), ("relaxed_simd", simd),
                                                          ("bulk_memory_opt", bulk)))):
            return finish("receipt-mismatch")
        row["compiler_sha256"], row["sysroot_sha256"] = receipt["compiler_sha256"], receipt["sysroot_sha256"]
        row["decode"] = capture([args.decoder, "--functions", wasm], out, "decode", args.compile_timeout)
        if row["decode"].get("returncode") != 0:
            return finish("decode-failed")
        counts, functions = decode_log(out / "decode.out")
        widths = []
        imports = list(inspect(wasm.read_bytes(), memory_limits=target.threads, memory_types=widths))
        row["instruction_evidence"] = instruction_evidence(target, simd, bulk, counts, functions, widths)
        owner = memory_owner(out, target, imports, uleb) if target.threads else None
        if owner:
            row["owner_sha256"] = digest(owner)
        for engine in ("int", "aot"):
            cmd = runtime_args(args.vm, engine, target, imports, owner, wasm)
            run = capture(cmd, out, engine, args.run_timeout)
            observed = (out / (engine + ".out")).read_bytes()
            run["output_sha256"] = hashlib.sha256(observed).hexdigest()
            run["bytes"] = len(observed)
            run["status"] = ("pass" if run.get("returncode") == 0 and observed == expected
                             else "timeout" if "timeout_seconds" in run else "execution-failed" if run["returncode"]
                             else "output-mismatch")
            if observed != expected:
                run["first_difference"] = next((i for i, pair in enumerate(zip(expected, observed))
                                                if pair[0] != pair[1]), min(len(expected), len(observed)))
            row["runs"][engine] = run
        if row["instruction_evidence"]["errors"]:
            return finish("instruction-mismatch")
        return finish("pass" if all(r["status"] == "pass" for r in row["runs"].values()) else "execution-failed")
    except (ValueError, OSError, KeyError, TypeError, IndexError) as error:
        row["error"] = str(error)
        return finish("harness-error")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("cc-sdk", "cxx-sdk", "objc-sdk", "objcpp-sdk", "vm", "decoder", "work"):
        p.add_argument("--" + flag, type=lambda s: Path(s).resolve(), required=flag in ("vm", "decoder", "work"))
    p.add_argument("--language", choices=LANGUAGES)
    p.add_argument("--profile", choices=[t.name for t in TARGETS])
    for flag in ("simd", "bulk"):
        p.add_argument("--" + flag, choices=("on", "off"))
    p.add_argument("--seed", type=lambda s: int(s, 0), help="seed for the reproducible random inputs")
    p.add_argument("--random-cases", type=int, default=4)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--compile-timeout", type=int, default=240)
    p.add_argument("--run-timeout", type=int, default=180)
    add_vm_identity_options(p)
    args = p.parse_args()
    if not (0 < args.jobs and 1 <= args.random_cases <= 64 and args.compile_timeout > 0 and args.run_timeout > 0):
        p.error("choose positive job and time limits, and 1 to 64 random cases")
    langs = [args.language] if args.language else list(LANGUAGES)
    if any(getattr(args, LANGUAGES[l][0]) is None for l in langs):
        p.error("supply the installed SDK root for each selected language")
    if args.work.exists() and any(args.work.iterdir()):
        p.error("choose an empty work directory")
    selected = [t for t in TARGETS if not args.profile or t.name == args.profile]
    def variants(value):
        return [False, True] if value is None else [value == "on"]
    entries = list(itertools.product(langs, selected, variants(args.simd), variants(args.bulk)))
    vm = verified_vm(args)
    seed = secrets.randbits(64) if args.seed is None else args.seed
    generator = random.Random(seed)
    seeds = [*FIXED, *(generator.getrandbits(32) for _ in range(args.random_cases))]
    expected = oracle(seeds)
    args.work.mkdir(parents=True, exist_ok=True)
    (args.work / "expected.bin").write_bytes(expected)
    # All four selections install the same imports.py and artifacts.py.
    sdk = getattr(args, LANGUAGES[langs[0]][0])
    sys.path.insert(0, str(sdk / "install"))
    from imports import inspect
    from artifacts import uleb
    meta = {"vm": vm, "decoder_sha256": digest(args.decoder), "runner_sha256": digest(Path(__file__)),
            "runtime_runner_sha256": digest(HERE / "sysroot_suite.py"),
            "fixtures": {p.name: digest(p) for p in sorted(FIXTURES.glob("probe.*"))},
            "frontends": {l: digest(getattr(args, LANGUAGES[l][0]) / "bin" / LANGUAGES[l][1]) for l in langs},
            "policies": {}, "planned_cells": len(entries), "seed": seed, "fixed_cases": list(FIXED),
            "random_cases": seeds[len(FIXED):], "expected_bytes": len(expected),
            "expected_sha256": hashlib.sha256(expected).hexdigest()}
    for l in langs:
        root = getattr(args, LANGUAGES[l][0])
        inputs = ["install/" + name for name in ("imports.py", "artifacts.py", "qualification.py", "compiler.py",
                                                   "frontend.py", "optional_isa.py", "scalar_memory.c")]
        inputs.append("src/compilers/objc/driver/policy.py" if l in ("objc", "objcpp") else "install/cc_policy.py")
        meta["policies"][l] = {path: digest(root / path) for path in inputs}
    (args.work / "inputs.json").write_text(json.dumps(meta, indent=2) + "\n")
    statuses, executions = Counter(), Counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool, (args.work / "results.jsonl").open("x") as log:
        tasks = [pool.submit(run_cell, args, *cell, seeds, expected, inspect, uleb) for cell in entries]
        for task in as_completed(tasks):
            row = task.result()
            print(json.dumps(row, separators=(",", ":")), file=log, flush=True)
            print(row["language"], row["profile"], f"simd={int(row['simd'])} bulk={int(row['bulk'])}", row["status"], flush=True)
            statuses[row["status"]] += 1
            executions.update(run["status"] for run in row["runs"].values())
    summary = {**meta, "cells": dict(statuses), "executions": dict(executions)}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if statuses == {"pass": len(entries)} and executions == {"pass": len(entries) * 2} else 1


if __name__ == "__main__":
    sys.exit(main())
