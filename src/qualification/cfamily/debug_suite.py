#!/usr/bin/env python3
"""Exercise four installed C-family frontends with live DWARF debugging, full restore and signed updates."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import platform
import re
import resource
import subprocess
import sys
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import debug_live as live
from sysroot_suite import (SHARED_MEMORY_PAGES, Target, add_vm_identity_options, capture,
                           digest, runtime_args, verified_vm, vm_elf_host)

PROTOCOL_SOURCE_COMMIT = "454a19a3c8c1ea388472d44589a126554067ef8b"
SUPPORT = {
    "tools/debug/snapshot.py": "7ac44f511b3e7fd83fc26523c8aec4919bb1ee58cc8cab5ea86d8389f904a59b",
    "test/0018.debugger/run_dump_launch_policy.py": "545069e4a2ff31d6948215113911375a929b638fb40ff489d915a1326d970be5",
    "test/0017.runtime/run_signed_update_boundaries.py": "121c640ffa9f15af367cae3379a72c943493c19b0797b84aac4eaf90f87298f7",
}
CAPABILITIES = ("source-debug", "full-dump-restore", "signed-hot-update")
PROFILES = [Target(*v) for v in itertools.product((32, 64), (False, True), (False, True), (False, True))]


class Frontend(NamedTuple):
    sdk_option: str
    driver: str
    extension: str
    standard: str
    source_function: str


LANGUAGES = {
    "c": Frontend("cc", "wrc", "c", "c17", "_start"),
    "cpp": Frontend("cxx", "wrcc", "cpp", "c++20", "_start"),
    "objc": Frontend("objc", "wroc", "m", "c17", "_c_QualificationReading__adjust_"),
    "objcpp": Frontend("objcpp", "wrocxx", "mm", "c++20", "_c_QualificationReading__adjust_"),
}
ENGINES = ("int", "aot")


def saved(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def support_modules(root):
    # snapshot is the only upstream import of the launch helper. Register that
    # exact checked module before loading the helper from a relocated subset.
    modules = []
    for relative, expected in SUPPORT.items():
        path = root / relative
        live.need(digest(path) == expected, f"changed VM support file: {relative}")
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


def installed_sdk(prefix, language):
    selection = prefix / "selection.json"
    record = json.loads(selection.read_bytes())
    frontend = "bin/" + LANGUAGES[language].driver
    actual = digest(prefix / frontend)
    live.need(record["language"] == language and re.fullmatch(r"[0-9a-f]{40}", record["commit"])
              and record["files"][frontend]["sha256"] == actual, f"installed {language} selection mismatch")
    return {**{key: record[key] for key in ("commit", "host", "platform", "language", "mode")},
            "selection_sha256": digest(selection), "frontend_sha256": actual}


def inspect_wasm(path, api, profile, source_function):
    from artifacts import sections
    data = path.read_bytes()
    widths = []
    imports = list(api.inspect(data, memory_limits=True, memory_types=widths))
    live.need(widths == [profile.address_bits], f"wrong Wasm memory width: {widths}")
    metadata = {}
    exports = {}
    function_names = {}
    structure = []
    bodies = []
    for start, end, name, body in sections(data):
        section = data[start]
        if section == 10:
            for _ in range(body.count()):
                bodies.append(hashlib.sha256(body.take(body.uint())).hexdigest())
            body.end()
        else:
            structure.append((section, name, hashlib.sha256(data[start:end]).hexdigest()))
        if name is not None and name.startswith(".debug_"):
            payload = body.data[body.position:]
            metadata[name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        if name == "name":
            while body.position < len(body.data):
                kind = body.byte()
                subsection = api.Reader(body.take(body.uint()))
                if kind == 1:
                    for _ in range(subsection.count()):
                        index = subsection.uint()
                        function_names[index] = subsection.name()
                    subsection.end()
        if section == 7:
            for _ in range(body.count()):
                export_name = body.name()
                exports[export_name] = (body.byte(), body.uint())
            body.end()
    for name in (".debug_info", ".debug_abbrev", ".debug_line", ".debug_str"):
        live.need(name in metadata and metadata[name]["bytes"] > 0, f"absent or empty DWARF section {name}: {path}")
    for name in ("value", "_start"):
        live.need(name in exports and exports[name][0] == 0, f"absent function export {name}: {path}")
    imported_functions = sum(i["kind"] == 0 for i in imports)
    # wasm-ld may export a .command_export wrapper. Its business-call index
    # includes imports. Signed function scopes select the changed local body.
    source_entry, = [i for i, spelling in function_names.items() if spelling == "_start"]
    source_index, = [i for i, spelling in function_names.items() if spelling == source_function]
    source_value, = [i for i, spelling in function_names.items() if spelling == "value"]
    local_index = source_value - imported_functions
    live.need(0 <= local_index < len(bodies) and exports["value"][1] >= imported_functions,
              "expected local business implementation and approved export")
    return ({"wasm": str(path), "sha256": digest(path), "dwarf": metadata, "imports": imports,
             "profile": profile.to_dict(), "entry_index": exports["_start"][1], "source_entry_index": source_entry,
             "source_function": source_function, "source_function_index": source_index,
             "value_index": exports["value"][1], "value_implementation_index": source_value,
             "value_local_index": local_index}, structure, bodies)


def build_pair(args, target, language, out, api):
    from artifacts import check_object, read_bounded
    from guest_profile import Profile
    sdk = args.sdks[language]
    config = LANGUAGES[language]
    src = HERE / "debug_fixtures" / ("probe." + config.extension)
    frontend = sdk / "bin" / config.driver
    profile = Profile(target.bits, "3.0", target.threads, target.mte, "eh" if target.eh else "noeh")
    base = [frontend, "--target", f"wasm{target.bits}", "--core", "3.0", "--std", config.standard, "-O0", "-g",
            "--mte" if target.mte else "--no-mte", "--eh" if target.eh else "--no-eh",
            "--threads" if target.threads else "--no-threads"]
    link = ["--reactor", "--export", "_start", "--export", "value"]
    if target.threads:
        base += ["-D", "SDK_SHARED=1"]
        link += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES), "--export", "wasi_thread_start"]
    build = {"profile": target.name, "language": language, "source": str(src), "source_sha256": digest(src),
             "frontend_sha256": digest(frontend), "generations": [], "compile": [], "module": 1 if target.threads else 0}
    structure = []
    bodies = []
    try:
        objc = language in ("objc", "objcpp")
        if objc:
            # wroc/wrocxx authenticate each sealed input object against the
            # active compiler and GNUstep closure before linking it.
            runtime_path = sdk / "share/uwros/objc" / profile.triple / profile.flavor / "runtime.json"
            runtime_hash = digest(runtime_path)
            runtime = json.loads(runtime_path.read_bytes())
            live.need(runtime["format"] == "uwros-gnustep-guest-v2" and runtime["profile"] == profile.to_dict(),
                      f"installed GNUstep runtime profile mismatch: {runtime_path}")
            build["runtime_receipt"] = {"path": str(runtime_path), "sha256": runtime_hash}
        for n, value in enumerate((17, 29), 1):
            path = out / f"generation-{n}.wasm"
            compile_args = [*base, "-D", f"SDK_GENERATION={value}"]
            if objc:
                obj = path.with_suffix(".o")
                command = [*compile_args, "-c", src, "-o", obj]
            else:
                command = [*compile_args, *link, "--build-receipt", src, "-o", path]
            result = capture(command, out, f"compile-{n}", args.compile_timeout)
            build["compile"].append(result)
            live.need(result.get("returncode") == 0, f"generation {n} compilation failed: {result}")
            if objc:
                note = check_object(read_bounded(obj), profile.to_dict(), build["frontend_sha256"], runtime_hash)
                result = capture([*base, *link, obj, "-o", path], out, f"link-{n}", args.compile_timeout)
                build.setdefault("link", []).append(result)
                live.need(result.get("returncode") == 0, f"generation {n} link failed: {result}")
            image, layout, functions = inspect_wasm(path, api, profile, config.source_function)
            structure.append(layout)
            bodies.append(functions)
            if objc:
                image.update(object=str(obj), sealed_object_sha256=digest(obj), object_note=note,
                             compiler_sha256=note["compiler_sha256"], sysroot_sha256=runtime["sysroot_sha256"])
            else:
                receipt_path = path.with_suffix(".wasm.wros-build.json")
                receipt = json.loads(receipt_path.read_bytes())
                live.need((receipt["artifact_sha256"], receipt["profile"], receipt["language"], receipt["settings"]) ==
                          (image["sha256"], image["profile"], language, {"optimization": "0", "debug": True}),
                          f"frontend receipt differs from requested profile or bytes: {receipt_path}")
                image.update(receipt_sha256=digest(receipt_path), compiler_sha256=receipt["compiler_sha256"],
                             sysroot_sha256=receipt["sysroot_sha256"])
            build["generations"].append(image)
        one, two = build["generations"]
        for key in ("imports", "entry_index", "source_entry_index", "source_function_index", "value_index", "value_implementation_index",
                    "value_local_index", "compiler_sha256", "sysroot_sha256"):
            live.need(one[key] == two[key], f"generations disagree on {key}")
            build[key] = one[key]
        changed = [i for i, (a, b) in enumerate(zip(*bodies)) if a != b]
        build["update_layout"] = {"identical_non_code_sections": structure[0] == structure[1],
                                  "same_function_count": len(bodies[0]) == len(bodies[1]), "changed_local_bodies": changed}
        build["owner"] = None
        if target.threads:
            memory, = [item for item in build["imports"] if item["kind"] == 2]
            flags, minimum, maximum = memory["limits"]
            live.need((memory["module"], memory["name"], flags, maximum) ==
                      ("env", "memory", 7 if target.bits == 64 else 3, SHARED_MEMORY_PAGES),
                      "invalid shared memory import")
            wat, owner = out / "owner.wat", out / "owner.wasm"
            width = "i64 " if target.bits == 64 else ""
            wat.write_text(f'(module (memory (export "memory") {width}{minimum} {maximum} shared))\n')
            assembly = capture([args.wrwat, wat, "--target", f"wasm{target.bits}", "--core", "3.0", "--threads",
                                "-o", owner], out, "assemble-owner", args.compile_timeout)
            build["assemble_owner"] = assembly
            live.need(assembly.get("returncode") == 0, f"shared memory owner assembly failed: {assembly}")
            build.update(owner=str(owner), owner_sha256=digest(owner))
        build["status"] = "built"
    except Exception as exc:
        build.update(status="build-failed", error=f"{type(exc).__name__}: {exc}")
    saved(out / "build.json", build)
    return build


def classify_launch_failure(row, target, log):
    # A closed socket, a signal or QEMU failure alone says nothing about an engine capability.
    if row.get("process_exit") != 126 or "debugger_status_reply" in row:
        return None
    clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log)
    patterns = []
    if row["expected"] == "reject-int-debug":
        patterns.append(("interpreter-debug-unsupported", "debug-jit is unsupported in the current mode: uwvm-int/full."))
    if row["engine"] == "int" and row["capability"] == "signed-hot-update":
        patterns.append(("interpreter-signed-update-unsupported", "update requires LLVM full, key/contract/scope and an independent direct-parent Unix stream"))
    if target.threads and row["capability"] == "signed-hot-update":
        patterns.append(("production-update-requires-single-owned-module", "production update profile requires a single owned module without a start section"))
    for code, expected in patterns:
        for line in clean.splitlines():
            if expected in line:
                row["vm_diagnostic"] = line
                return code
    return None


def run_cell(args, target, language, engine, capability, build, out, support):
    folder = out / engine / capability
    folder.mkdir(mode=0o700, parents=True)
    row = {"round": args.round_id, "host": args.host, "profile": target.name,
           "language": language, "engine": engine, "capability": capability,
           "vm": args.identity, "sdk": args.selections[language], "build": str(out.relative_to(args.work) / "build.json"),
           "build_sha256": digest(out / "build.json"), "positive": False, "attempted": False,
           "expected": "reject-int-debug" if engine == "int" and capability != "signed-hot-update" else "measure"}
    if build["status"] != "built":
        row.update(status="build-blocked", error=build["error"])
        saved(folder / "result.json", row)
        return row
    row["guest_sha256"] = [gen["sha256"] for gen in build["generations"]]
    vm = None
    snapshot, launch, protocol = support
    try:
        base = list(map(str, runtime_args(args.vm, engine, target, build["imports"], build["owner"],
                                          build["generations"][0]["wasm"])))
        if capability == "full-dump-restore" and not any(i["module"] == "wasi_snapshot_preview1" for i in build["imports"]):
            # A visible WASIp1 environment needs a source-bound builtin import
            # to be captured. This guest and its optional memory-only owner have none.
            base[base.index("--wasip1-single-enable")] = "--wasip1-single-disable"
        if engine == "aot" and capability != "signed-hot-update":
            # Use the VM's diagnostic defaults, as the upstream restore and stepping runners do.
            i = base.index("--runtime-llvm-jit-policy")
            del base[i:i + 2]
        if capability == "signed-hot-update":
            live.update_probe(args, row, build, base, folder, protocol)
            layout = build["update_layout"]
            live.need(layout["identical_non_code_sections"] and layout["same_function_count"]
                      and layout["changed_local_bodies"] == [build["value_local_index"]],
                      f"frontend images exceed the signed function scope: {layout}")
        else:
            command = [base[0], "-Rdbg", "--debug-permissions", "full", *base[1:]]
            row["argv"] = [*args.runner, command[0], "--debug-jit-control-fd", "<inherited>", *command[1:]]
            vm = launch.VM(command, folder, args.runner, stdin=subprocess.DEVNULL)
            row["pid"] = vm.process.pid
            row["channel"] = "direct-parent/AF_UNIX/SOCK_SEQPACKET/SO_PASSCRED"
            vm.channel.settimeout(args.run_timeout)
            if row["expected"] == "reject-int-debug":
                row["debugger_status_reply"] = vm.request("status")
                raise ValueError(f"ordinary debugger admitted an explicitly selected interpreter: {row['debugger_status_reply']}")
            if capability == "source-debug":
                live.debug_probe(vm, row, build, target, args.run_timeout)
            else:
                live.dump_probe(vm, row, build, target, args.run_timeout, folder, snapshot,
                                restore_timeout=args.restore_timeout)
            row["process_exit"] = vm.process.wait(timeout=args.run_timeout)
            live.need(row["process_exit"] == 0, f"debugged VM exit {row['process_exit']}")
        row.update(status="pass", positive=True)
    except live.Limitation as exc:
        row.update(status="unsupported", limitation=str(exc))
    except live.RestoreRefusal as exc:
        row.update(status="restore-declined", limitation=str(exc))
    except Exception as exc:
        row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        if vm is not None:
            # Compute the real pre-cleanup exit on a closed channel. Upstream's close
            # retires only this pidfd and may kill a still-attached debug server.
            if row["status"] == "failed":
                exit_timeout = args.run_timeout if row["expected"] == "reject-int-debug" else .5
                try:
                    row["process_exit"] = vm.process.wait(timeout=exit_timeout)
                except subprocess.TimeoutExpired:
                    pass
            row["commands"] = [item for i, item in enumerate(vm.commands)
                               if not i or item != vm.commands[i - 1]]
            vm.close()
            row["retired_process_exit"] = vm.process.returncode
        row["attempted"] = "pid" in row
        log = folder / "vm.log"
        if log.is_file():
            row["log_sha256"] = digest(log)
            if row["status"] == "failed":
                limitation = classify_launch_failure(row, target, log.read_text(errors="replace"))
                if limitation:
                    outcome = "expected-rejection" if row["expected"] == "reject-int-debug" else "unsupported"
                    row.update(status=outcome, limitation=limitation)
                    if outcome == "expected-rejection":
                        row["assertion"] = "pass"
                    row.pop("error", None)
        saved(folder / "result.json", row)
    return row


def execute(args, target, language, api, support):
    folder = args.work / target.name / language
    folder.mkdir(mode=0o700, parents=True)
    build = build_pair(args, target, language, folder, api)
    return [run_cell(args, target, language, e, c, build, folder, support)
            for e, c in itertools.product(args.engines, args.capabilities)]


def isolation_receipt():
    # The host launching the namespace can retain the exact enclosing slice receipt.
    info = {"controller_machine": platform.machine(), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "cgroup": Path("/proc/self/cgroup").read_text().strip(),
            "namespaces": {k: os.readlink("/proc/self/ns/" + k) for k in ("mnt", "net", "pid")}}
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("vm", "vm-support", "work"):
        p.add_argument("--" + name, required=True, type=lambda path: Path(path).resolve())
    for config in LANGUAGES.values():
        p.add_argument(f"--{config.sdk_option}-sdk", type=lambda path: Path(path).resolve())
    add_vm_identity_options(p)
    p.add_argument("--wrwat", type=lambda path: Path(path).resolve(), help="installed WAT frontend, required with threads")
    p.add_argument("--profile", action="append", choices=[t.name for t in PROFILES])
    p.add_argument("--engine", action="append", choices=ENGINES)
    p.add_argument("--language", action="append", choices=LANGUAGES)
    p.add_argument("--capability", action="append", choices=CAPABILITIES)
    p.add_argument("--runner-json", type=Path, help="JSON array of host runner arguments preceding the target VM ELF")
    p.add_argument("--round-id", default=uuid.uuid4().hex, help="shared label for the five hosts in one acceptance run")
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--run-timeout", type=int, default=60)
    p.add_argument("--restore-timeout", type=int, default=900,
                   help="total seconds for synchronous snapshot preparation and all pending restore replies")
    p.add_argument("--compile-timeout", type=int, default=180)
    args = p.parse_args()
    targets = [t for t in PROFILES if not args.profile or t.name in args.profile]
    args.engines = list(dict.fromkeys(args.engine or ["aot"]))
    languages = list(dict.fromkeys(args.language or LANGUAGES))
    args.capabilities = list(dict.fromkeys(args.capability or CAPABILITIES))
    if ("int" in args.engines and any(c != "signed-hot-update" for c in args.capabilities)
            and (len(targets), len(languages), len(args.capabilities)) != (1, 1, 1)):
        p.error("an INT debugger rejection probe requires one --profile, one --language and one --capability")
    args.sdks = {lang: getattr(args, LANGUAGES[lang].sdk_option + "_sdk") for lang in languages}
    for lang, sdk in args.sdks.items():
        if sdk is None:
            p.error(f"--{LANGUAGES[lang].sdk_option}-sdk is required for {lang}")
    if any(t.threads for t in targets) and not args.wrwat:
        p.error("thread profiles require --wrwat")
    if min(args.jobs, args.run_timeout, args.restore_timeout, args.compile_timeout) < 1:
        p.error("jobs and timeouts must be positive")
    if not re.fullmatch("[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", args.round_id):
        p.error("choose a 1–80 character round ID using letters, numbers, dots, dashes or underscores")
    if any(args.work.is_relative_to(path) for path in ("/tmp", "/dev/shm")):
        p.error("choose a work directory on the qualification volume")
    if args.work.exists() and any(args.work.iterdir()):
        p.error("choose an empty work directory for this run")
    args.runner = json.loads(args.runner_json.read_bytes()) if args.runner_json else []
    if not isinstance(args.runner, list) or not all(isinstance(x, str) and x for x in args.runner):
        p.error("--runner-json must contain an argv array")
    args.identity = verified_vm(args)
    args.host = vm_elf_host(args.vm)
    live.need(args.host is not None, "unsupported target VM ELF architecture")
    os.umask(0o077)
    args.work.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp = args.work / ".tmp"
    temp.mkdir(mode=0o700)
    for name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[name] = str(temp)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.path.insert(0, str(args.sdks[languages[0]] / "install"))
    import imports
    args.selections = {lang: installed_sdk(sdk, lang) for lang, sdk in args.sdks.items()}
    support = support_modules(args.vm_support)
    planned = len(targets) * len(languages) * len(args.engines) * len(args.capabilities)
    metadata = {"schema": "wros-cfamily-debug-v1", "round": args.round_id,
                "started_utc": datetime.now(timezone.utc).isoformat(), "vm": args.identity, "host": args.host,
                "isolation": isolation_receipt(), "runner": args.runner, "support_sha256": SUPPORT,
                "protocol_source_commit": PROTOCOL_SOURCE_COMMIT, "installed_selections": args.selections,
                "profiles": [t.name for t in targets], "languages": languages, "engines": args.engines,
                "capabilities": args.capabilities, "planned": planned,
                "suite_sha256": {f.name: digest(f) for f in (Path(__file__), HERE / "debug_live.py", HERE / "sysroot_suite.py")},
                "producer_frontends": {str(args.sdks[lang] / "bin" / LANGUAGES[lang].driver): selection["frontend_sha256"]
                                       for lang, selection in args.selections.items()},
                "wrwat_sha256": digest(args.wrwat) if args.wrwat else None}
    saved(args.work / "inputs.json", metadata)
    counts, limits = Counter(), Counter()
    with (args.work / "results.jsonl").open("x") as results, ThreadPoolExecutor(max_workers=args.jobs) as pool:
        tasks = [pool.submit(execute, args, target, lang, imports, support) for target, lang in itertools.product(targets, languages)]
        for task in as_completed(tasks):
            for row in task.result():
                print(json.dumps(row, separators=(",", ":")), file=results, flush=True)
                counts[row["status"]] += 1
                if "limitation" in row:
                    limits[row["limitation"]] += 1
                print(row["host"], row["profile"], row["language"], row["engine"], row["capability"], row["status"], flush=True)
    complete = sum(counts.values()) == planned and not (counts["failed"] or counts["build-blocked"])
    passed = counts["pass"] + counts["expected-rejection"] == planned
    summary = {"round": args.round_id, "ended_utc": datetime.now(timezone.utc).isoformat(),
               "planned": planned, "reported": sum(counts.values()), "positive": counts["pass"],
               "expected_rejections_passed": counts["expected-rejection"], "measurements_complete": complete, "passed": passed,
               "outcomes": dict(counts), "limitations": dict(limits), "inputs_sha256": digest(args.work / "inputs.json"),
               "results_sha256": digest(args.work / "results.jsonl")}
    saved(args.work / "summary.json", summary)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
