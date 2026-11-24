#!/usr/bin/env python3
"""Check ordinary four-byte Wasm accesses against the allocation tags on live test buffers."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from optional_isa_suite import LANGUAGES, TARGETS, decode_log, memory_owner
from sysroot_suite import SHARED_MEMORY_PAGES, add_vm_identity_options, capture, digest, runtime_args, verified_vm

FIXTURES = HERE / "memtag_fixtures"
FRAME = struct.Struct("<6Q")
ENGINES = ("int", "aot")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cases(target, exhaustive):
    bits = 4 if target.bits == 32 else 8
    sample = [0, *(1 << i for i in range(bits)), (1 << bits) - 1]
    for mode in range(4):
        deltas = range(1 << bits) if exhaustive and mode < 2 else sample
        for delta in deltas if target.mte else [0]:
            phase = ("mismatch-trap" if delta else "matching-tag") if target.mte else "ordinary-control"
            yield mode, delta, phase
    if target.mte:
        yield 4, 0, "allocator-live"
        yield 5, 0, "allocator-retired-shadow"


def instruction_evidence(wasm, log, target, api):
    from artifacts import sections
    data = wasm.read_bytes()
    widths = []
    imports = api.inspect(data, memory_limits=target.threads, memory_types=widths)
    counts, functions = decode_log(log)
    require(widths == [target.bits] and counts["shared_memories"] == int(target.threads), "memory profile differs")
    require(target.eh or not (counts["eh_total"] or counts["tags"]), "EH enabled in a no-EH module")
    require(target.threads or not (counts["threads_total"] or counts["thread_spawn_imports"]), "unexpected threads")
    require(bool(counts["memtag_total"]) == target.mte, "final WasmMTE instruction count differs from profile")
    header = log.read_text().splitlines()[0]
    tags = json.loads(header.split(" memtag=", 1)[1].split(" threads=", 1)[0])
    if target.mte:
        ops = {"MemtagLoad", "MemtagExtract", "MemtagInsert", "MemtagStore", "MemtagStorez", "MemtagUntagstorez"}
        require(ops <= tags.keys(), "final module lacks the fixture's tag operations")
        require("MemtagRelease" in tags and {"MemtagClaim", "MemtagClaimz", "MemtagReserve"} & tags.keys(),
                "linked module lacks managed allocation and release")

    # LLD can export a command wrapper which calls the identically named leaf.
    # Identify the leaf and read its operands at instruction boundaries.
    imported = sum(i["kind"] == 0 for i in imports)
    indices = {f["name"]: index for index, f in functions.items() if not f["calls"]}
    expected = {indices[name] - imported: name for name in ("read_word", "write_word")}
    leaves = {}
    for start, _, _, section in sections(data):
        if data[start] != 10:
            continue
        for local in range(section.count()):
            body = api.Reader(section.take(section.uint()))
            if local not in expected:
                continue
            name = expected[local]
            store = name == "write_word"
            require(body.uint() == 0, f"{name}: unexpected locals")
            expr = body.position
            for param in range(2 if store else 1):
                require(body.byte() == 0x20 and body.uint() == param, f"{name}: expected local.get {param}")
            offset = body.position - expr
            require(body.byte() == (0x36 if store else 0x28), f"{name}: expected four-byte scalar instruction")
            alignment = body.uint()
            require(alignment <= 2 and body.uint(target.bits) == 0, f"{name}: wrong memory immediate")
            require(bytes(body.take(len(body.data) - body.position)) in (b"\x0b", b"\x0f\x0b"),
                    f"{name}: unexpected instruction after access")
            leaves[name] = {"opcode": "i32.store" if store else "i32.load", "function": local + imported,
                            "expression_offset": offset, "alignment_log2": alignment}
        section.end()
    require(len(leaves) == 2, "missing exported scalar bodies")
    return {"whole_module": counts, "memtag_opcodes": tags, "scalar_accesses": leaves}, imports


def check_run(target, mode, delta, phase, engine, evidence, stdout, stderr, run):
    fault = phase == "mismatch-trap"
    require(run.get("returncode") == run["expected_returncode"], "unexpected exit or timeout")
    require(len(stdout) == FRAME.size + (0 if fault else 4), "incorrect phase/output length")
    actual_mode, actual_delta, address, logical, first, last = FRAME.unpack_from(stdout)
    require((actual_mode, actual_delta) == (mode, delta), "wrong guest case")
    bits = 4 if target.bits == 32 else 8
    mask = (1 << bits) - 1
    require(0 < address < 1 << (target.bits - (bits if target.mte else 0)), "invalid untagged address")
    require(max(logical, first, last) <= mask, "tag outside the pointer-width domain")
    require(address % 16 == (14 if mode in (2, 3) else 0), "wrong access placement")
    run["observed"] = {"address": address, "pointer_tag": logical, "first_tag": first, "last_tag": last}
    if mode >= 4:
        expected = logical if mode == 4 else 0
        require(logical and first == last == expected, "allocator shadow observation differs")
    elif not target.mte:
        require(logical == first == last == 0, "unexpected control metadata")
    elif mode < 2:
        require(first and first == last and logical ^ first == delta, "single-granule tags differ")
    else:
        require(logical and logical == first and logical ^ last == delta, "straddling tags differ")
    if not fault:
        require(stdout[FRAME.size:] == bytes(4) and "[crash]" not in stderr and "host_denied_" not in stderr,
                "access or allocator observation did not complete cleanly")
        return
    lines = stderr.splitlines()
    require(lines.count("uwvm: [crash] memory-protection") == 1 and
            "  Reason: memory tag mismatch" in lines and "  Exit status: 122" in lines and
            "  Backend: " + ("LLVM" if engine == "aot" else "interpreter") in lines, "wrong VM fault")
    leaf = evidence["scalar_accesses"]["write_word" if mode & 1 else "read_word"]
    expected = {"Memory index": 0, "Wasm function": leaf["function"], "Pointer tag": logical,
                "Allocation tag": last, "Pointer": (logical << (target.bits - bits)) | address,
                "Granule": (address + 3) & ~15}
    for label, value in expected.items():
        require(lines.count(f"  {label}: {value}") == 1, f"wrong fault {label}")
    offsets = re.findall(r"^  Wasm byte offset: (\d+|unavailable)$", stderr, re.M)
    require(len(offsets) == 1 and offsets[0] in (str(leaf["expression_offset"]), "unavailable"),
            "wrong fault instruction offset")
    run["fault"] = {**expected, "wasm_byte_offset": None if offsets[0] == "unavailable" else int(offsets[0])}


def run_cell(args, language, target, api, uleb):
    option, driver, extension, standard = LANGUAGES[language]
    out = args.work / language / target.name
    out.mkdir(parents=True)
    row = {"language": language, "profile": target.name, "directory": str(out.relative_to(args.work)), "runs": []}
    try:
        wasm = out / "guest.wasm"
        sources = []
        for source in sorted(FIXTURES.glob("*.c")):
            if not target.mte and source.stem == "allocation_lifecycle":
                continue
            # Each installed frontend must parse every translation unit in its own dialect.
            path = out / source.with_suffix(extension).name
            shutil.copyfile(source, path)
            sources.append(path)
        cmd = [getattr(args, option) / "bin" / driver, "--target", f"wasm{target.bits}", "--core", "3.0",
               "--std", standard, "-O3", "-g", "--threads" if target.threads else "--no-threads",
               "--eh" if target.eh else "--no-eh", "--mte" if target.mte else "--no-mte",
               "--build-receipt", "-I", FIXTURES, "-D", f"TEST_MTE={int(target.mte)}",
               "--export", "read_word", "--export", "write_word"]
        if target.threads:
            cmd += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)]
        row["compile"] = capture([*cmd, *sources, "-o", wasm], out, "compile", args.compile_timeout)
        require(row["compile"].get("returncode") == 0, "compile failed or timed out")
        receipt_path = out / "guest.wasm.wros-build.json"
        receipt = json.loads(receipt_path.read_bytes())
        profile = {"address_bits": target.bits, "wasm_version": "3.0", "threads": target.threads,
                   "mte": target.mte, "exceptions": "eh" if target.eh else "noeh"}
        row.update(wasm_sha256=digest(wasm), receipt_sha256=digest(receipt_path))
        require(receipt["artifact_sha256"] == row["wasm_sha256"] and receipt["language"] == language and
                all(receipt["profile"].get(k) == v for k, v in profile.items()), "compile receipt differs")
        for key in ("compiler_sha256", "sysroot_sha256"):
            require(re.fullmatch("[0-9a-f]{64}", receipt[key]), "invalid " + key)
            row[key] = receipt[key]
        row["decode"] = capture([args.decoder, "--functions", wasm], out, "decode", args.compile_timeout)
        require(row["decode"].get("returncode") == 0, "decode failed or timed out")
        evidence, imports = instruction_evidence(wasm, out / "decode.out", target, api)
        row.update(instruction_evidence=evidence, imports=imports)
        owner = memory_owner(out, target, imports, uleb) if target.threads else None
        if owner:
            row["owner_sha256"] = digest(owner)
        for engine in args.engine:
            directory = out / engine
            directory.mkdir()
            matching_addresses = {}
            cmd = runtime_args(args.vm, engine, target, imports, owner, wasm)
            flags = ["--log-color", "disable"]
            if target.mte:
                flags += ["--runtime-memtag-backend", "software"]
            cmd[1:1] = flags
            for mode, delta, phase in cases(target, args.exhaustive):
                name = f"{mode}-{delta:03}"
                run = capture([*cmd, str(mode), f"{delta:03}"], directory, name, args.run_timeout)
                run.update(engine=engine, phase=phase, mode=mode, delta=delta, log_prefix=f"{engine}/{name}",
                           expected_returncode=122 if phase == "mismatch-trap" else 0)
                if mode < 4:
                    run.update(operation="write" if mode & 1 else "read", placement="straddling" if mode & 2 else "single")
                try:
                    check_run(target, mode, delta, phase, engine, evidence, (directory / (name + ".out")).read_bytes(),
                              (directory / (name + ".err")).read_text(errors="replace"), run)
                    if phase == "matching-tag":
                        matching_addresses[mode] = run["observed"]["address"]
                    if phase == "mismatch-trap":
                        require(run["observed"]["address"] == matching_addresses.get(mode),
                                "untagged address differs from the matching access")
                    run["status"] = "pass"
                except ValueError as error:
                    run.update(status="failed", error=str(error))
                row["runs"].append(run)
        row["status"] = "pass" if all(run["status"] == "pass" for run in row["runs"]) else "failed"
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        row.update(status="failed", error=str(error))
    (out / "result.json").write_text(json.dumps(row, indent=2) + "\n")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("cc-sdk", "cxx-sdk", "objc-sdk", "objcpp-sdk", "vm", "decoder", "work"):
        parser.add_argument("--" + option, type=lambda value: Path(value).resolve(),
                            required=option in ("vm", "decoder", "work"))
    parser.add_argument("--language", action="append", choices=LANGUAGES)
    parser.add_argument("--profile", action="append", choices=[t.name for t in TARGETS])
    parser.add_argument("--engine", action="append", choices=ENGINES)
    parser.add_argument("--exhaustive", action="store_true", help="all tag differences on single-granule accesses")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--compile-timeout", type=int, default=240)
    parser.add_argument("--run-timeout", type=int, default=180)
    add_vm_identity_options(parser)
    args = parser.parse_args()
    languages = list(dict.fromkeys(args.language or LANGUAGES))
    targets = [t for t in TARGETS if not args.profile or t.name in args.profile]
    args.engine = list(dict.fromkeys(args.engine or ENGINES))
    if min(args.jobs, args.compile_timeout, args.run_timeout) < 1:
        parser.error("jobs and timeouts must be positive")
    if any(getattr(args, LANGUAGES[l][0]) is None for l in languages):
        parser.error("supply the installed SDK root for each selected language")
    if args.work.exists() and any(args.work.iterdir()):
        parser.error("choose an empty work directory")
    vm = verified_vm(args)
    args.work.mkdir(parents=True, exist_ok=True)
    scratch = args.work / "tmp"
    scratch.mkdir()
    os.environ["TMPDIR"] = str(scratch)
    sdk = getattr(args, LANGUAGES[languages[0]][0])
    sys.path.insert(0, str(sdk / "install"))
    import imports
    from artifacts import uleb
    cells = list(itertools.product(languages, targets))
    planned = sum(1 for _, t in cells for _ in args.engine for _ in cases(t, args.exhaustive))
    meta = {"vm": vm, "engines": args.engine, "exhaustive": args.exhaustive, "planned_cells": len(cells),
            "planned_executions": planned, "decoder_sha256": digest(args.decoder),
            "sources": {str(p.relative_to(HERE)): digest(p) for p in [Path(__file__).resolve(), HERE / "sysroot_suite.py",
                        HERE / "optional_isa_suite.py", *sorted(FIXTURES.iterdir())] if p.is_file()},
            "frontends": {l: digest(getattr(args, LANGUAGES[l][0]) / "bin" / LANGUAGES[l][1]) for l in languages},
            "installed_readers": {p: digest(sdk / "install" / p) for p in ("artifacts.py", "imports.py")}}
    (args.work / "inputs.json").write_text(json.dumps(meta, indent=2) + "\n")
    statuses, executions, phases = Counter(), Counter(), Counter()
    with ThreadPoolExecutor(args.jobs) as pool, (args.work / "results.jsonl").open("x") as rows:
        for row in pool.map(lambda cell: run_cell(args, *cell, imports, uleb), cells):
            print(json.dumps(row), file=rows, flush=True)
            print(row["language"], row["profile"], row["status"], flush=True)
            statuses[row["status"]] += 1
            executions.update(r["status"] for r in row["runs"])
            phases.update(r["phase"] for r in row["runs"] if r["status"] == "pass")
    summary = {**meta, "cells": statuses, "executions": executions, "phases": phases}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return int(statuses != {"pass": len(cells)} or executions != {"pass": planned})


if __name__ == "__main__":
    sys.exit(main())
