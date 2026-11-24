#!/usr/bin/env python3
"""Compare both edges of each SIMD and memory.copy/fill switch in an archived ISA matrix."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ENGINES = ("int", "aot")
SWITCH = (False, True)
FILES = ("inputs.json", "summary.json", "results.jsonl", "expected.bin")
THREAD_BULK = {"MemoryInit", "DataDrop", "passive data segment", "data count section"}
LEGACY_POLICIES = {
    "a91d2d93fb18243f039b6fb55af3f981937b7a4af2d13cd33cf78e099fc989b7": "producer defaults",
    "38eb6a91ac8d07aa50f0ce39d7af7966306d88c38f7773b794ac59829be3b0ba": "SIMD disables only",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def producer(directory):
    # Import only from the explicitly supplied SDK source tree, never from evidence paths.
    policy = directory.parents[1] / "compilers/cc/policy"
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(directory), str(policy)]
    import optional_isa_suite as suite
    import sysroot_suite as runtime
    import imports as wasm
    for module, source in ((suite, directory / "optional_isa_suite.py"), (runtime, directory / "sysroot_suite.py"),
                           (wasm, policy / "imports.py")):
        require(Path(module.__file__).resolve() == source.resolve(), f"wrong producer source for {source}")
    return suite, runtime, wasm


def source_inputs(root, profiles, tools, pins):
    suite, _, _ = tools
    meta = read(root / "inputs.json")
    for key in ("runner_sha256", "runtime_runner_sha256", "decoder_sha256", "fixtures"):
        require(meta[key] == pins[key], f"{root}: {key} differs from the supplied producer")
    require(set(meta["frontends"]) == set(meta["policies"]) == set(suite.LANGUAGES), "expected all four frontends")
    for language in suite.LANGUAGES:
        require(meta["policies"][language]["install/imports.py"] == pins["imports_sha256"], f"{language}: imports reader differs")
    for field, length in (("commit", 40), ("tree", 40), ("sha256", 64), ("receipt_sha256", 64)):
        require(re.fullmatch(f"[0-9a-f]{{{length}}}", meta["vm"][field]), f"invalid VM {field}")
    generator = random.Random(meta["seed"])
    randoms = meta["random_cases"]
    require(type(meta["seed"]) is int and 1 <= len(randoms) <= 64 and meta["fixed_cases"] == list(suite.FIXED)
            and randoms == [generator.getrandbits(32) for _ in randoms], f"{root}: seed sequence differs")
    seeds = [*suite.FIXED, *randoms]
    expected = suite.oracle(seeds)
    require((root / "expected.bin").read_bytes() == expected and sha(expected) == meta["expected_sha256"]
            and len(expected) == meta["expected_bytes"], f"{root}: independent oracle differs")
    count = len(profiles) * len(suite.LANGUAGES) * 4
    summary = read(root / "summary.json")
    require(meta["planned_cells"] == count and summary == {**meta, "cells": {"pass": count},
            "executions": {"pass": 2 * count}}, f"{root}: incomplete or unsuccessful original summary")
    return meta, seeds, expected


def compile_proof(row, directory, target, seeds, suite):
    language, simd, bulk = row["language"], row["simd"], row["bulk"]
    _, driver, extension, standard = suite.LANGUAGES[language]
    compile = row["compile"]
    argv = compile["argv"]
    source, guest = Path(argv[-3]), Path(argv[-1])
    require(source.is_absolute() and source.parts[-2:] == ("optional_isa_fixtures", "probe" + extension),
            "wrong input fixture")
    require(guest.is_absolute() and tuple(guest.parts[-4:]) == (*Path(row["directory"]).parts, "guest.wasm"),
            "wrong linked module path")
    flags = ["--target", f"wasm{target.bits}", "--core", "3.0", "-O3", "-g", "--std", standard,
             "--threads" if target.threads else "--no-threads", "--eh" if target.eh else "--no-eh",
             "--mte" if target.mte else "--no-mte", "-msimd128" if simd else "-mno-simd128",
             "-mbulk-memory-opt" if bulk else "-mno-bulk-memory-opt", "--build-receipt",
             "--export", "isa_vector", "--export", "isa_move", "--export", "isa_fill",
             "-D", "ISA_SEEDS=" + ",".join(f"0x{x:08x}u" for x in seeds)]
    if target.threads:
        flags.extend(("--shared-memory-pages", str(suite.SHARED_MEMORY_PAGES)))
    require(Path(argv[0]).name == driver and argv[1:] == [*flags, str(source), "-o", str(guest)]
            and compile == {"argv": argv, "returncode": 0}, "compile command or exit differs")
    receipt_file = directory / "guest.wasm.wros-build.json"
    receipt = read(receipt_file)
    require(digest(receipt_file) == row["receipt_sha256"] and receipt["format"] == "wros-build-receipt"
            and receipt["language"] == language, "build receipt differs")
    for key in ("compiler_sha256", "sysroot_sha256"):
        require(re.fullmatch(r"[a-f0-9]{64}", row[key]) and row[key] == receipt[key], f"build receipt {key} differs")
    require(digest(directory / "guest.wasm") == receipt["artifact_sha256"] == row["wasm_sha256"], "guest digest differs")
    profile = {"address_bits": target.bits, "threads": target.threads, "mte": target.mte,
               "exceptions": "eh" if target.eh else "noeh", "wasm_version": "3.0"}
    require(all(receipt["profile"][k] == v for k, v in profile.items()), "build profile differs")
    settings = {"simd128": simd, "relaxed_simd": simd, "bulk_memory_opt": bulk}
    require(all(receipt["optional_isa"][k] is v for k, v in settings.items()), "build switches differ")
    return str(guest), (argv[0], str(source), row["compiler_sha256"], row["sysroot_sha256"])


def owner_proof(wasm, directory, row, target, imports, guest, pages):
    path = directory / "owner.wasm"
    if not target.threads:
        require("owner_sha256" not in row and not path.exists(), "unexpected shared memory owner")
        return None
    memory, = (item for item in imports if item["kind"] == 2)
    flags, low, high = memory["limits"]
    require((memory["module"], memory["name"]) == ("env", "memory")
            and flags == (7 if target.bits == 64 else 3) and 0 < low <= high == pages, "wrong imported memory")
    require(digest(path) == row["owner_sha256"], "shared memory owner digest differs")
    reader = wasm.Reader(path.read_bytes())
    wasm.require_core(reader)
    require(reader.byte() == 5, "missing owner memory")
    body = wasm.Reader(reader.take(reader.uint()))
    require(body.uint() == 1 and body.limits() == memory["limits"], "owner memory limits differ")
    body.end()
    require(reader.byte() == 7, "missing owner export")
    body = wasm.Reader(reader.take(reader.uint()))
    require(body.uint() == 1 and body.name() == "memory" and body.byte() == 2 and body.uint() == 0, "wrong owner export")
    body.end()
    reader.end()
    return str(Path(guest).with_name("owner.wasm"))


def decode_proof(row, directory, target, tools, decoder, guest, controls):
    suite, _, wasm = tools
    actual = directory / "guest.wasm"
    argv = row["decode"]["argv"]
    require(row["decode"] == {"argv": argv, "returncode": 0} and argv[1:] == ["--functions", guest],
            "wrong original decoder invocation")
    listing = directory / "decode.out"
    saved = listing.read_bytes()
    fresh = subprocess.run([decoder, "--functions", actual], stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
    old_prefix, new_prefix = (b"MODULE " + str(path).encode() + b" " for path in (guest, actual))
    require(fresh.returncode == 0 and fresh.stderr == (directory / "decode.err").read_bytes() == b""
            and saved.startswith(old_prefix) and fresh.stdout.startswith(new_prefix)
            and fresh.stdout[len(new_prefix):] == saved[len(old_prefix):], "fresh whole-module decode differs")
    requirements = {}
    modern = controls == "decoded requirements"
    if modern:
        counts, functions = suite.decode_log(listing, bulk_requirements=requirements)
        enabled = row["bulk"] or bool(requirements)
        require(row["vm_bulk_memory"] == {"enabled": enabled, "requirements_beyond_copy_fill": requirements},
                "VM bulk-memory requirements differ")
    else:
        counts, functions = suite.decode_log(listing)
        enabled = True
        require("vm_bulk_memory" not in row, "unexpected runtime policy field for this producer")
        header = saved.split(b"\n", 1)[0]
        requirements = json.loads(header.rsplit(b" other_bulk_ops=", 1)[1])
    widths = []
    imports = wasm.inspect(actual.read_bytes(), memory_limits=target.threads, memory_types=widths)
    proof = suite.instruction_evidence(target, row["simd"], row["bulk"], counts, functions, widths)
    require(not proof["errors"] and proof == row["instruction_evidence"] and 0 < len(functions) <= counts["bodies"],
            "whole-module or workload instruction evidence differs")
    thread_init = target.threads and {"MemoryInit", "DataDrop"} <= requirements.keys() <= THREAD_BULK
    if row["bulk"]:
        group = "copy-fill-enabled"
    elif not modern:
        group = "legacy-default-thread-initialization" if thread_init else "legacy-default-bulk-memory"
    elif not enabled:
        group = "full-bulk-memory-disabled"
    elif thread_init:
        group = "thread-initialization"
    else:
        group = "other-bulk-requirement"
    return imports, enabled, group, sha(saved)


def cell(row, root, target, tools, decoder, seeds, expected, controls):
    suite, runtime, wasm = tools
    relative = Path(row["language"]) / target.name / f"simd-{int(row['simd'])}-bulk-{int(row['bulk'])}"
    require(str(relative) == row["directory"], "wrong cell directory")
    directory = root / relative
    require(row == read(directory / "result.json") and row["status"] == "pass" and set(row["runs"]) == set(ENGINES),
            "original cell and execution records disagree")
    guest, source = compile_proof(row, directory, target, seeds, suite)
    imports, enabled, group, decode_hash = decode_proof(row, directory, target, tools, decoder, guest, controls)
    owner = owner_proof(wasm, directory, row, target, imports, guest, suite.SHARED_MEMORY_PAGES)
    results, streams = {}, {}
    vm = row["runs"]["int"]["argv"][0]
    for engine in ENGINES:
        run = row["runs"][engine]
        if controls == "decoded requirements":
            argv = suite.optional_runtime_args(vm, engine, target, imports, owner, guest, simd=row["simd"], bulk_memory=enabled)
        else:
            argv = runtime.runtime_args(vm, engine, target, imports, owner, guest)
            if controls == "SIMD disables only" and not row["simd"]:
                start = argv.index("--run")
                argv[start:start] = ["--wasm-feature-disable-simd", "--wasm-feature-disable-relaxed-simd"]
        require(run["argv"] == argv, f"{engine} invocation differs")
        stdout = (directory / (engine + ".out")).read_bytes()
        stderr = (directory / (engine + ".err")).read_bytes()
        require(type(run["returncode"]) is int and run["returncode"] == 0 and "timeout_seconds" not in run
                and run["status"] == "pass", f"{engine} did not complete successfully")
        require(stdout == expected and sha(stdout) == run["output_sha256"] and len(stdout) == run["bytes"],
                f"{engine} raw stdout differs from its digest or oracle")
        results[engine] = {"exit": run["returncode"], "stdout": stdout, "stderr": stderr}
        streams[engine] = {"exit": run["returncode"], "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}
    proof = {"module_sha256": row["wasm_sha256"], "receipt_sha256": row["receipt_sha256"],
             "decode_sha256": decode_hash, "bulk_memory": group, "runs": streams}
    return results, (*source, vm), proof


def qualify(args):
    tools = producer(args.suite_dir)
    suite, _, wasm = tools
    targets = {t.name: t for t in suite.TARGETS}
    profiles = args.profile or list(targets)
    require(set(profiles) <= targets.keys() and len(set(profiles)) == len(profiles), "invalid or duplicate profile")
    root = args.results
    grouped = not (root / "inputs.json").exists()
    batches = [(root / p, [p]) for p in profiles] if grouped else [(root, profiles)]
    fixtures = ["probe.h", *("probe" + spec[2] for spec in suite.LANGUAGES.values())]
    pins = {"runner_sha256": digest(args.suite_dir / "optional_isa_suite.py"),
            "runtime_runner_sha256": digest(args.suite_dir / "sysroot_suite.py"), "decoder_sha256": digest(args.decoder),
            "imports_sha256": digest(Path(wasm.__file__)), "fixtures": {f: digest(suite.FIXTURES / f) for f in fixtures}}
    controls = "decoded requirements" if hasattr(suite, "optional_runtime_args") else LEGACY_POLICIES[pins["runner_sha256"]]
    report = {"checker_sha256": digest(Path(__file__)), "producer": pins, "profiles": profiles, "source_results": {},
              "runtime_feature_controls": controls,
              "bulk_memory_cells": Counter(), "cell_evidence": {}, "differences": []}
    receipt = None
    if args.qualification_receipt:
        receipt = read(args.qualification_receipt)
        receipt_hash = digest(args.qualification_receipt)
        require(not args.receipt_sha256 or receipt_hash == args.receipt_sha256, "qualification receipt digest differs")
        require(all(re.fullmatch("[a-f0-9]{40}", receipt[k]) for k in ("sdk_commit", "sdk_tree")), "invalid SDK identity")
        report["qualification"] = {**{k: receipt[k] for k in ("sdk_commit", "sdk_tree", "host")}, "sha256": receipt_hash}
        require(receipt["matrix"]["planned"] == len(receipt["matrix"]["profiles"]) * len(suite.LANGUAGES) * 4,
                "invalid qualification receipt plan")
    cells, sources = {}, {}
    for directory, selected in batches:
        meta, seeds, expected = source_inputs(directory, selected, tools, pins)
        identity = {k: meta[k] for k in ("vm", "frontends", "policies")}
        require(report.setdefault("identity", identity) == identity, "mixed VM or frontend identities")
        label = selected[0] if len(selected) == 1 else "all"
        paths = {name: digest(directory / name) for name in FILES}
        if receipt:
            require(len(selected) == 1 and receipt["matrix"]["profiles"][label] == paths, "original profile receipt differs")
            if "vm" in receipt:
                require(all(receipt["vm"][k] == meta["vm"][k] for k in ("commit", "tree", "sha256"))
                        and receipt["decoder_sha256"] == pins["decoder_sha256"], "qualification VM or decoder differs")
        report["source_results"][label] = {"files": paths, "seed": meta["seed"], "cases": seeds}
        plan = set(itertools.product(suite.LANGUAGES, selected, SWITCH, SWITCH))
        with (directory / "results.jsonl").open("rb") as stream:
            for number, line in enumerate(stream, 1):
                row = json.loads(line)
                key = (row["language"], row["profile"], row["simd"], row["bulk"])
                require(type(key[2]) is bool and type(key[3]) is bool and key in plan and key not in cells,
                        f"{directory}, row {number}: duplicate or unplanned cell {key}")
                try:
                    results, source, proof = cell(row, directory, targets[key[1]], tools, args.decoder, seeds, expected, controls)
                except (ValueError, OSError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as exc:
                    raise ValueError(f"{row['directory']}: {exc}") from exc
                require(sources.setdefault(key[:2], source) == source, f"{key}: compiler, source, sysroot or VM path differs")
                report["cell_evidence"][row["directory"]] = proof
                report["bulk_memory_cells"][proof["bulk_memory"]] += 1
                cells[key] = results
        missing = plan - cells.keys()
        require(not missing, f"{directory}: missing cells {sorted(missing)}")
    comparisons = {engine: {family: {"compared": 0, "equivalent": 0} for family in ("simd", "copy_fill")} for engine in ENGINES}
    for language, profile, simd, bulk in cells:
        for family, switch, peer in (("simd", simd, (True, bulk)), ("copy_fill", bulk, (simd, True))):
            if switch:
                continue
            for engine, total in comparisons.items():
                off = cells[language, profile, simd, bulk][engine]
                on = cells[language, profile, *peer][engine]
                different = [field for field in off if off[field] != on[field]]
                total[family]["compared"] += 1
                total[family]["equivalent"] += int(not different)
                if different:
                    report["differences"].append({"language": language, "profile": profile, "engine": engine,
                        "switch": family, "fixed_switch_enabled": bulk if family == "simd" else simd, "fields": different})
    return {**report, "cells": len(cells), "comparisons": comparisons, "passed": not report["differences"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True, help="one suite work directory or a parent of profile directories")
    parser.add_argument("--decoder", type=Path, required=True, help="original native qualification decoder")
    parser.add_argument("--suite-dir", type=Path, default=HERE, help="trusted matching SDK src/qualification/cfamily")
    parser.add_argument("--profile", action="append", help="exact profile to verify (repeatable, default all sixteen)")
    parser.add_argument("--qualification-receipt", type=Path, help="published aggregate ISA qualification.json for per-profile outputs")
    parser.add_argument("--receipt-sha256", help="trusted SHA-256 of the supplied qualification receipt")
    parser.add_argument("--output", type=Path, help="create a new JSON report (default stdout)")
    args = parser.parse_args()
    args.suite_dir, args.results, args.decoder = (p.resolve() for p in (args.suite_dir, args.results, args.decoder))
    if args.receipt_sha256 and not args.qualification_receipt:
        parser.error("--receipt-sha256 requires --qualification-receipt")
    if args.output and (args.output.exists() or args.output.resolve().is_relative_to(args.results)):
        parser.error("choose a new report path outside the original evidence")
    try:
        report = qualify(args)
    except (ValueError, OSError, ImportError, KeyError, AttributeError, TypeError, IndexError, subprocess.SubprocessError) as exc:
        report = {"passed": False, "error": str(exc)}
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(body)
        print(json.dumps({k: report[k] for k in ("passed", "cells", "comparisons", "error") if k in report}))
    else:
        sys.stdout.write(body)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
