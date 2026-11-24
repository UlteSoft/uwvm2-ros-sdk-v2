"""Replay the original, non-MTE cells from a production C/C++ sysroot matrix."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import re
import sys

from optional_isa_suite import PROFILE_KEYS, fields
from sysroot_suite import (SHARED_MEMORY_PAGES, Target, capture, digest, missing_link_symbol,
                           qualification_outcome, validate_thread_budgets, verified_vm, vm_elf_host)
from wasmtime_reference.adapter import (WASMTIME_COMMIT, WASMTIME_VERSION, checked_hash, compare_engines,
                                        recorded_policy, require, run_host, saved_engines)

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent
ENGINES = ("int", "aot")
EVIDENCE_ERRORS = (AttributeError, ImportError, IndexError, KeyError, OSError, TypeError, ValueError)
LIMITATIONS = {"dependency-unavailable", "upstream-skip", "invalid-upstream-test",
               "unsupported-import", "unsupported-grant", "unsupported-import-and-grant"}
LSEARCH = "upstream/libc-test/src/functional/search_lsearch.c"
LSEARCH_BLOB = "711a7a085d86e5baca49d61e7907c6fd37d4426d"


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def production(args, manifest, cases):
    inputs_path, records_path, summary_path = (args.results / name for name in ("inputs.json", "results.jsonl", "summary.json"))
    inputs, summary = read_json(inputs_path), read_json(summary_path)
    checked_hash(SUITE / "cases.json", inputs["manifest_sha256"])
    checked_hash(SUITE / "sysroot_suite.py", inputs["runner_sha256"])
    require(inputs["upstreams"] == manifest["upstreams"], "original upstream revisions differ")
    require(all(summary[k] == value for k, value in inputs.items()), "original inputs and summary disagree")
    vm = inputs["vm"]
    for key, length in (("commit", 40), ("tree", 40), ("sha256", 64), ("receipt_sha256", 64)):
        require(re.fullmatch("[0-9a-f]{%d}" % length, vm[key]), f"invalid original VM {key}")
    require(vm["sha256"] == inputs["vm_sha256"], "original VM digests differ")
    if args.vm:
        require(verified_vm(args) == vm, "original VM differs from the supplied executable, receipt or target")

    targets = [Target(*axes) for axes in itertools.product((32, 64), (False, True), (False, True), (False, True))]
    selection = inputs.get("selection", {})
    require(not selection or selection.keys() == {"sources", "profiles"}, "invalid original selection fields")
    sources = selection.get("sources", list(cases))
    profiles = selection.get("profiles", [t.name for t in targets])
    require(set(sources) <= cases.keys() and set(profiles) <= {t.name for t in targets}
            and len(set(sources)) == len(sources) and len(set(profiles)) == len(profiles), "invalid original selection")
    plan = {(t.name, src): t for t in targets if t.name in profiles for src in sources
            if t.threads or cases[src]["family"] != "Open POSIX"}
    require(len(plan) == inputs["planned_builds"] and len({src for _, src in plan}) == inputs["distinct_sources"],
            "original plan size differs from the manifest and profile selection")
    rows = {}
    builds, runs, outcomes = Counter(), Counter(), Counter()
    with records_path.open() as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["profile"], row["source"])
            require(key in plan and key not in rows, f"unplanned or duplicate original cell {key}")
            case = cases[key[1]]
            require(row["family"] == case["family"] and row.get("sdk_case") == case.get("sdk_case")
                    and row["vm"] == vm, f"original source, case provenance or VM differs for {key}")
            require(row["qualification"] == qualification_outcome(case, row), f"incorrect original qualification for {key}")
            rows[key] = row
            builds[row["status"]] += 1
            runs.update(run["status"] for run in row["runs"].values())
            outcomes[row["qualification"]] += 1
    require(rows.keys() == plan.keys(), f"original matrix is missing {len(plan) - len(rows)} cells")
    suite_exit = 1 if outcomes["failed"] else (77 if outcomes["pass"] != len(plan) else 0)
    require((dict(builds), dict(runs), dict(outcomes), suite_exit) ==
            (summary["builds"], summary["executions"], summary["qualification"], summary["exit_code"]),
            "original status totals or exit code disagree with its rows")
    evidence = {"original_inputs_sha256": digest(inputs_path), "original_results_sha256": digest(records_path),
                "original_summary_sha256": digest(summary_path), "original_planned_cells": len(plan),
                "original_selection": selection or "full matrix", "vm": vm, "original_suite_exit": suite_exit,
                "manifest_sha256": inputs["manifest_sha256"], "suite_policy_sha256": inputs["runner_sha256"],
                "upstreams": inputs["upstreams"], "original_decoder_sha256": inputs["decoder_sha256"],
                "original_wrwat_sha256": inputs["wrwat_sha256"], "original_cc_sha256": inputs["cc_sha256"],
                "original_cxx_sha256": inputs["cxx_sha256"]}
    if args.vm:
        evidence["vm_target_sha256"] = digest(args.vm_target)
        evidence["source_host"] = vm_elf_host(args.vm)
    if args.qualification_receipt:
        proof = read_json(args.qualification_receipt)
        require(proof["complete"] is True and proof["rows"] == len(plan) and proof["exit"] == suite_exit
                and proof["results_sha256"] == evidence["original_results_sha256"]
                and proof["summary_sha256"] == evidence["original_summary_sha256"] and proof["summary"] == summary,
                "production qualification receipt disagrees with original evidence")
        evidence["qualification_receipt_sha256"] = digest(args.qualification_receipt)
    non_mte = {key: target for key, target in plan.items() if not target.mte}
    require(non_mte, "the original selection includes no non-MTE cases")
    return non_mte, rows, evidence


def source_digests(compiler_sources, manifest, selected):
    for project, key in (("llvm", "llvm_git_blobs"), ("libc-test", "libc_test_git_blobs")):
        for relative, expected in manifest[key].items():
            data = (SUITE / "upstream" / project / relative).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            require(blob == expected, f"upstream Git blob differs for {project}/{relative}")
    return {case["path"]: digest((compiler_sources if case["family"] == "Open POSIX" and "sdk_case" not in case
                                  else SUITE) / case["path"]) for case in manifest["cases"] if case["path"] in selected}


def compile_evidence(row, case, target, relative, original, result):
    argv = row["compile"]["argv"]
    cxx = case["family"] == "libc++" or case.get("language") == "cpp"
    flags = ["--target", f"wasm{target.bits}", "--core", "3.0", "--std", "c++20" if cxx else "c17", "-O1",
             "--no-mte", "--eh" if target.eh else "--no-eh", "--threads" if target.threads else "--no-threads", "--build-receipt"]
    if target.threads:
        flags += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)]
    guest = Path(argv[-1])
    require(guest.is_absolute() and guest.parts[-(len(relative.parts) + 1):] == (*relative.parts, "guest.wasm"),
            "original compile output belongs to another source/profile")
    # Reconstruct the producer's absolute paths, including the common libc-test units.
    family = case["family"]
    source_count = 5 if family == "libc-test" else 1
    source = Path(argv[-source_count - 2])
    path = Path(case["path"])
    require(source.is_absolute() and source.parts[-len(path.parts):] == path.parts, "compiled source path differs")
    source_root = source.parents[len(path.parts) - 1]
    sources = [source]
    include = Path(argv[-source_count - 3])
    if family == "Open POSIX":
        flags += ["-D", "_POSIX_C_SOURCE=200809L", "-D", "_WASI_EMULATED_SIGNAL",
                  "-lwasi-emulated-signal", "-lwasi-emulated-getpid"]
        include_path = Path("wasi-libc/test/open-posix-test-suite/include")
        if "sdk_case" not in case:
            require(include == source_root / include_path, "Open POSIX sources and headers are from different roots")
    elif family == "libc-test":
        flags += ["-D", "_GNU_SOURCE"]
        include_path = Path("upstream/libc-test/src/common")
        require(include == source_root / include_path, "libc-test support directory differs")
        sources += [include / f for f in ("print.c", "path.c", "rand.c", "utf8.c")]
    elif cxx:
        if "ADDITIONAL_COMPILE_FLAGS(has-fconstexpr-steps): -fconstexpr-steps=20000000" in (SUITE / path).read_text():
            flags += ["--constexpr-steps", "20000000"]
        include_path = Path("upstream/llvm/libcxx/test/support")
        require(include == source_root / include_path, "libc++ support directory differs")
    else:
        include_path = Path("llvm-project/compiler-rt/lib/builtins")
    require(include.is_absolute() and include.parts[-len(include_path.parts):] == include_path.parts,
            "original include path disagrees with the case family")
    expected = [*flags, "-I", include, *sources, "-o", guest]
    require(Path(argv[0]).name == ("wrcc" if cxx else "wrc") and argv[1:] == list(map(str, expected)),
            "original compile command differs from the selected profile or case inputs")
    result.update(compile_stdout_sha256=digest(original / "compile.out"), compile_stderr_sha256=digest(original / "compile.err"))
    return guest


def verify_owner(reader, data, limits):
    # The producer emits one memory definition and one export. A subtype with
    # different bounds, an initializer, or a second module cannot stand in for it.
    binary = reader.Reader(data)
    reader.require_core(binary)
    sections = []
    while binary.position < len(binary.data):
        section = binary.byte()
        body = reader.Reader(binary.take(binary.uint()))
        if section == 0:
            continue
        sections.append(section)
        require(body.uint() == 1, "unexpected owner section size")
        if section == 5:
            require(list(body.limits()) == limits, "owner and guest memory limits differ")
        else:
            require(section == 7 and body.name() == "memory" and body.byte() == 2 and body.uint() == 0,
                    "owner does not export its memory at index zero")
        body.end()
    require(sections == [5, 7], "unexpected shared memory owner sections")


def decode_counts(path, guest_path):
    with path.open() as stream:
        header = stream.readline().rstrip("\n")
    prefix = f"MODULE {guest_path} "
    require(header.startswith(prefix), "decoder receipt names a different guest")
    return fields(" " + header[len(prefix):], PROFILE_KEYS)


def linked_evidence(args, row, case, target, saved_guest, original, out, result):
    guest = original / "guest.wasm"
    checked_hash(guest, row["wasm_sha256"])
    require(row["compile"].get("returncode") == 0 and row["runs"].keys() == set(ENGINES),
            "linked row has no successful compile or lacks an engine")
    receipt_path = original / "guest.wasm.wros-build.json"
    receipt = read_json(receipt_path)
    triple = f"wasm{target.bits}-wasip1" + ("-threads" if target.threads else "")
    profile = {"address_bits": target.bits, "wasm_version": "3.0", "threads": target.threads, "mte": False,
               "exceptions": "eh" if target.eh else "noeh", "triple": triple, "memtag_wire": None,
               "extensions": ["threads"] if target.threads else [],
               "abi": "wasi_snapshot_preview1" if target.bits == 32 else "uwvm-preview1-memory64-extension"}
    language = "cpp" if case["family"] == "libc++" or case.get("language") == "cpp" else "c"
    require(receipt["format"] == "wros-build-receipt" and receipt["language"] == language and receipt["profile"] == profile
            and receipt["mode"] == "off" and receipt["artifact_sha256"] == row["wasm_sha256"]
            and receipt["compiler_sha256"] == row["compiler_sha256"] and receipt["settings"]["optimization"] == "1"
            and all(re.fullmatch("[0-9a-f]{64}", receipt[key]) for key in ("compiler_sha256", "sysroot_sha256"))
            and receipt.get("shared_memory_pages") == (SHARED_MEMORY_PAGES if target.threads else None),
            "compiler receipt disagrees with original guest, compiler, language or non-MTE profile")
    result.update(build_receipt_sha256=digest(receipt_path), compiler_sha256=receipt["compiler_sha256"],
                  sysroot_sha256=receipt["sysroot_sha256"])
    require(row["decode"].get("returncode") == 0 and row["decode"]["argv"][1:] == [str(saved_guest)], "invalid original decode command")
    decoded = capture([args.decoder, guest], out, "decode", args.timeout)
    result["decode"] = {**decoded, "stdout_sha256": digest(out / "decode.out"), "stderr_sha256": digest(out / "decode.err")}
    require(decoded.get("returncode") == 0, "reference decoder failed or timed out")
    counts = decode_counts(out / "decode.out", guest)
    require(counts == decode_counts(original / "decode.out", saved_guest) and counts["bodies"] > 0
            and {k: v for k, v in counts.items() if k != "bodies"} == row["opcodes"], "instruction evidence differs")
    require(counts["memtag_total"] == 0 and counts["shared_memories"] == int(target.threads)
            and (target.threads or not (counts["thread_spawn_imports"] or counts["threads_total"]))
            and (target.eh or not (counts["eh_total"] or counts["tags"])), "guest instructions disagree with profile")
    widths = []
    imports = args.reader.inspect(guest.read_bytes(), memory_limits=True, memory_types=widths)
    for item in imports:
        if "limits" in item:
            item["limits"] = list(item["limits"])
        if item["module"] == "wasi_snapshot_preview1":
            require(item["kind"] == 0 and item["name"].endswith("_wasm64") == (target.bits == 64), "incorrect Preview1 ABI")
    require(imports == row["imports"] and widths == [target.bits], "guest imports, signatures or memory width differ")
    spawns = [item for item in imports if (item["module"], item["name"]) == ("wasi", "thread-spawn")]
    require(len(spawns) == counts["thread_spawn_imports"] and all(item["kind"] == 0 and item["params"] == ["i32"]
            and item["results"] == ["i32"] for item in spawns), "incorrect thread-spawn count or ABI")
    if case.get("realtime_sleep"):
        poll = "poll_oneoff_wasm64" if target.bits == 64 else "poll_oneoff"
        require(any(i["module"] == "wasi_snapshot_preview1" and i["name"] == poll for i in imports),
                "rwlock case lacks its required timer import")
    result.update(opcodes=counts, imports=imports)
    memories = [item for item in imports if item["kind"] == 2]
    if not target.threads:
        require(not memories and "memory_owner" not in row and not (original / "owner.wasm").exists(), "unexpected owner")
        return guest, None
    memory, = memories
    flags, low, high = memory["limits"]
    require((memory["module"], memory["name"], flags) == ("env", "memory", 7 if target.bits == 64 else 3)
            and 0 < low <= high == SHARED_MEMORY_PAGES, "unexpected shared memory import")
    owner = original / "owner.wasm"
    record = row["memory_owner"]
    require(record.get("returncode") == 0 and record["argv"][1:] == [str(saved_guest.with_name("owner.wat")), "--target",
            f"wasm{target.bits}", "--core", "3.0", "--threads", "-o", str(saved_guest.with_name("owner.wasm"))],
            "original shared memory owner command differs")
    result["owner_sha256"] = checked_hash(owner, record["sha256"])
    width = "i64 " if target.bits == 64 else ""
    require((original / "owner.wat").read_text() == f'(module (memory (export "memory") {width}{low} {high} shared))\n',
            "original owner WAT differs from the guest limits")
    verify_owner(args.reader, owner.read_bytes(), memory["limits"])
    return guest, owner


def reference_limits(row, target, policy):
    # host.cpp has no argument-vector, clock resolution, positioned read, or
    # thread-spawn implementation. Its poll_oneoff callback implements deny only.
    pointer = f"i{target.bits}"
    unavailable = {"args_get": [pointer, pointer], "args_sizes_get": [pointer, pointer],
                   "clock_res_get": ["i32", pointer], "fd_pread": ["i32", pointer, pointer, "i64", pointer]}
    imports, semantics = [], []
    for item in row["imports"]:
        module, name = item["module"], item["name"]
        if (module, name) == ("wasi", "thread-spawn"):
            imports.append("wasi.thread-spawn")
        elif module == "wasi_snapshot_preview1":
            base = name.removesuffix("_wasm64")
            if base in unavailable:
                require(item["params"] == unavailable[base] and item["results"] == ["i32"], f"unexpected {name} signature")
                imports.append(module + "." + name)
            if base == "poll_oneoff" and "allow=" + name in policy:
                require(item["params"] == [pointer] * 4 and item["results"] == ["i32"], f"unexpected {name} signature")
                semantics.append("allow=" + name)
    semantics.extend(option for option in policy if option in {"grant=args", "grant=monotonic-resolution", "grant=realtime-timer"})
    return imports, semantics


def cell(args, row, case, target, result):
    relative = Path(target.name) / case["family"] / Path(case["path"]).parent.name / Path(case["path"]).name
    original, out = args.results / relative, args.work / relative
    out.mkdir(parents=True)
    require(row["source_sha256"] == args.source_hashes[case["path"]], "original source SHA-256 differs")
    saved_guest = compile_evidence(row, case, target, relative, original, result)
    if row["status"] != "linked":
        require(not row["runs"], "unlinked original row contains engine runs")
        if row["status"] in ("compile-failed", "compile-timeout"):
            build = row["compile"]
            failed = type(build.get("returncode")) is int and build["returncode"] != 0
            timed_out = "timeout_seconds" in build and "returncode" not in build
            require((failed if row["status"] == "compile-failed" else timed_out)
                    and not (original / "guest.wasm").exists() and not (original / "guest.wasm.wros-build.json").exists()
                    and "wasm_sha256" not in row, "uncompiled cell has a guest or successful compile")
            if row["qualification"] == "dependency-unavailable":
                symbol = case["unavailable_link_symbol"]
                require(row["missing_link_symbol"] == symbol and row["compile"].get("returncode") == 1
                        and missing_link_symbol((original / "compile.err").read_text(errors="replace"), symbol),
                        "expected sole missing link dependency is unconfirmed")
                result["missing_link_symbol"] = symbol
                return "dependency-unavailable"
            return "not-compiled"
        return "original-build-error"

    guest, owner = linked_evidence(args, row, case, target, saved_guest, original, out, result)
    require(row["runs"]["int"]["argv"][0] == row["runs"]["aot"]["argv"][0], "original engine executable paths differ")
    policy = recorded_policy(row, target, case, args.vm)
    result["wasip1_policy"] = policy
    argv = row["runs"]["int"]["argv"]
    result["wasip1_limits"] = [argv[i + 2:i + 4] for i, flag in enumerate(argv) if flag == "--wasip1-single-limit"]
    result["engines"] = saved_engines(row, original)
    for engine, saved in row["runs"].items():
        if saved["status"] == "pass":
            output = (original / (engine + ".out")).read_bytes()
            require(saved.get("returncode") == 0 and "timeout_seconds" not in saved and not re.search(rb"\bskipped\b", output, re.I)
                    and ("pass_stdout_line" not in case or case["pass_stdout_line"].encode() in output.splitlines()),
                    f"original {engine} pass disagrees with its exit or output")
    if row["qualification"] == "upstream-skip":
        expected = case["upstream_skip_stdout"].encode()
        require(all((original / (e + ".out")).read_bytes() == expected for e in ENGINES), "upstream skip output differs")
        return "upstream-skip"
    if case["path"] == LSEARCH and args.invalid_lsearch:
        result["reason"] = "The upstream test supplies short string literals for lsearch's 80-byte records."
        return "invalid-upstream-test"
    imports, semantics = reference_limits(row, target, policy)
    result.update(unsupported_imports=imports, unsupported_semantics=semantics)
    if imports and semantics:
        return "unsupported-import-and-grant"
    if imports:
        return "unsupported-import"
    if semantics:
        return "unsupported-grant"
    require(not result["wasip1_limits"], "unrepresented interface limit in the reference policy")
    result["reference_eligible"] = True
    host = result["wasmtime"] = run_host(args, target, guest, owner, policy, out)
    result["engines"] = compare_engines(result["engines"], host)
    if "guest_exit_code" not in host:
        return host["termination"]
    verdicts = {engine["comparison"] for engine in result["engines"].values()}
    if "unavailable" in verdicts:
        return "comparison-unavailable"
    if "difference" in verdicts:
        return "difference"
    success_line = case.get("pass_stdout_line")
    if (host["guest_exit_code"] != 0 or row["qualification"] != "pass" or "upstream_skip_stdout" in case
            or (success_line and success_line.encode() not in (out / "stdout").read_bytes().splitlines())):
        return "guest-or-original-qualification-failed"
    return "match"


def replay(args, row, case, target):
    result = {k: row[k] for k in ("profile", "family", "source", "source_sha256", "wasm_sha256", "sdk_case") if k in row}
    result.update(original_build=row["status"], original_qualification=row["qualification"], owner_sha256=None,
                  reference_eligible=False, engines={e: {"comparison": "unavailable"} for e in ENGINES})
    try:
        result["status"] = cell(args, row, case, target, result)
    except EVIDENCE_ERRORS as exc:
        result.update(status="evidence-error", reason=str(exc))
    return result


def compare_sysroot(args):
    manifest = read_json(SUITE / "cases.json")
    cases = {case["path"]: case for case in manifest["cases"]}
    require(len(cases) == len(manifest["cases"]), "duplicate manifest source")
    validate_thread_budgets(manifest["cases"])
    plan, rows, evidence = production(args, manifest, cases)
    args.source_hashes = source_digests(args.compiler_sources, manifest, {src for _, src in plan})
    args.invalid_lsearch = manifest["libc_test_git_blobs"].get("src/functional/search_lsearch.c") == LSEARCH_BLOB
    args.decoder = args.decoder.resolve()
    reader_path = args.compiler_sources.resolve() / "policy/imports.py"
    sys.path.insert(0, str(reader_path.parent))
    import imports
    require(Path(imports.__file__).resolve() == reader_path.resolve(), "expected the matching SDK import reader")
    args.reader = imports
    host_hash = checked_hash(args.host, args.host_sha256) if args.host_sha256 else digest(args.host)
    meta = {**evidence, "suite": "sysroot", "reference": "Wasmtime C API with the C-family qualification host",
            "reference_machine": platform.machine(), "wasmtime_version": WASMTIME_VERSION, "wasmtime_release_commit": WASMTIME_COMMIT,
            "host_binary_sha256": host_hash, "host_source_sha256": digest(HERE / "host.cpp"),
            "decoder_sha256": digest(args.decoder), "imports_reader_sha256": digest(reader_path),
            "driver_sha256": digest(HERE / "compare.py"), "adapter_driver_sha256": digest(HERE / "adapter.py"),
            "sysroot_driver_sha256": digest(Path(__file__)), "decode_policy_sha256": digest(SUITE / "optional_isa_suite.py"),
            "planned_cells": len(plan), "excluded_mte_cells": evidence["original_planned_cells"] - len(plan),
            "guest_environment": [], "guest_preopens": [], "stdin": "EOF"}
    write_json(args.work / "inputs.json", meta)
    scratch = args.work / "scratch"
    scratch.mkdir()
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    statuses, qualifications, unsupported_imports, unsupported_semantics = Counter(), Counter(), Counter(), Counter()
    profiles, families, comparisons = defaultdict(Counter), defaultdict(Counter), {engine: Counter() for engine in ENGINES}
    eligible = starts = terminations = original_failures = 0
    log = args.work / "results.jsonl"
    with log.open("x") as stream, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(lambda k: replay(args, rows[k], cases[k[1]], plan[k]), plan):
            print(json.dumps(row, separators=(",", ":")), file=stream, flush=True)
            status = row["status"]
            statuses[status] += 1
            qualifications[row["original_qualification"]] += 1
            original_failures += row["original_qualification"] == "failed" and status != "invalid-upstream-test"
            profiles[row["profile"]][status] += 1
            families[row["family"]][status] += 1
            unsupported_imports.update(row.get("unsupported_imports", []))
            unsupported_semantics.update(row.get("unsupported_semantics", []))
            eligible += row["reference_eligible"]
            host = row.get("wasmtime", {})
            starts += host.get("start_invoked", False)
            terminations += "guest_exit_code" in host
            for engine in ENGINES:
                comparisons[engine][row["engines"][engine]["comparison"]] += 1
    complete = (sum(statuses.values()) == len(plan) and not original_failures and set(statuses) <= {"match", *LIMITATIONS}
                and starts == terminations == eligible == statuses["match"])
    code = (0 if statuses["match"] == len(plan) else 77) if complete else 1
    summary = {**meta, "statuses": statuses, "per_profile": profiles, "per_family": families,
               "original_qualifications": qualifications, "original_failures_excluding_invalid_tests": original_failures,
               "unsupported_imports": unsupported_imports, "unsupported_semantics": unsupported_semantics,
               "comparisons": comparisons, "planned_guests": eligible, "guest_starts": starts, "guest_terminations": terminations,
               "inputs_sha256": digest(args.work / "inputs.json"), "results_sha256": digest(log),
               "complete": complete, "passed": code == 0, "exit_code": code}
    write_json(args.work / "summary.json", summary)
    print(json.dumps(summary), flush=True)
    return code
