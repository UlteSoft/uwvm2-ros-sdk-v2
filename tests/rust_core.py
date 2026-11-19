"""Compile real Rust no_std source and exercise WasmMTE, proof-gated source attributes and VM grants."""
import argparse
import json
import re
from pathlib import Path
import os
import subprocess

from separate_compilation import Profile, cgroup_record, sha, candidate_arguments, candidate_command
from imports import inspect


def wasm_functions(listing):
    parts = re.split(r"(?m)^[0-9a-f]+ <([^>]+)>:\s*$", listing)
    return dict(zip(parts[1::2], parts[2::2]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("rustroot", "toolchain", "sysroots", "plain-sysroots", "runtime", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--sdk", type=Path, default=Path(__file__).resolve().parents[1])
    candidate_arguments(parser)
    args = parser.parse_args()
    sdk, work, rust, tool, runtime = [p.resolve() for p in
        (args.sdk, args.output, args.rustroot, args.toolchain, args.runtime)]
    source = Path(__file__).with_name("rust") / "core_body.rs"
    receipt = dict(cgroup=cgroup_record(), complete=False, cases=[], modules={})
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    app = sdk / "bin/wrrs"
    inputs = [Path(__file__), source, source.with_name("tagged_access.rs"), app, runtime, args.sysroots, args.plain_sysroots,
              rust / "bin/rustc", tool / "bin/clang", sdk / "language/rust/toolchain-inputs.json", sdk / "tools/wasm/tag_ir.cpp"]
    receipt["inputs"] = {str(p): sha(p) for p in inputs}
    report = work / "results.json"

    def save():
        report.write_text(json.dumps(receipt, indent=2) + "\n")

    def run(name, cmd, expected=True, diagnostic=None):
        command = candidate_command(cmd, args.candidate_mte)
        result = subprocess.run(command, capture_output=True, timeout=360, cwd=work)
        (work / (name + ".stdout")).write_bytes(result.stdout)
        (work / (name + ".stderr")).write_bytes(result.stderr)
        receipt["cases"].append(dict(name=name, exit=result.returncode, argv=command, expected=expected))
        save()
        if (result.returncode == 0) != expected or (diagnostic and diagnostic not in result.stderr):
            raise RuntimeError(f"{name} failed its check, see {report}")
        return result.stdout

    module = work / "body.wasm"
    base = [app, "--rustroot", rust, "--toolchain", tool, "--target", "wasm32", "--no-eh",
            "-O3", "-g", "--print-identity", "-o", module]
    for mode, closure, switches in (("tagged", args.sysroots, []), ("plain", args.plain_sysroots, ["--no-mte"])):
        build = [*base, "--sysroots", closure.resolve(), *switches]
        identity = json.loads(run("compile-" + mode, [*build, source]))
        profile = Profile(32, mte=mode == "tagged", exceptions="noeh")
        if identity["profile"] != profile.to_dict() or sha(module) != identity["module_sha256"]:
            raise RuntimeError("incorrect compilation identity")
        suppressions = identity["stages"]["wros_application"]["suppressions"]
        if suppressions["proof"] != "register-only-integer-ssa" or suppressions["globals"]:
            raise RuntimeError("unexpected Rust source proof")
        expected_elisions = {"proven_scalar"} if profile.mte else set()
        if set(suppressions["functions"]) != expected_elisions:
            raise RuntimeError("incorrect source-level elision inventory: " + str(suppressions))
        if profile.mte and (not {"safe_wrapper", "wide_word"}.issubset(suppressions["retained_functions"]) or
                            "__wros_no_memtag_state" not in suppressions["retained_globals"]):
            raise RuntimeError("a source annotation suppressed an unproven access")
        imports = inspect(module.read_bytes())
        if [(r["module"], r["name"]) for r in imports] != [("uwvm_ros_v2", "abi")]:
            raise RuntimeError("unexpected linked imports")
        listing = run("disassemble-" + mode, [tool / "bin/llvm-objdump", "-d", module]).decode()
        bodies = wasm_functions(listing)
        for function in ("tagged", "safe_wrapper"):
            body = bodies[function]
            if ("memtag." in body) != (mode == "tagged"):
                raise RuntimeError(f"{mode}: incorrect tag operations in {function}")
        scalar = bodies["proven_scalar"]
        if "i32.const" not in scalar or any(op in scalar for op in ("memtag.", ".load", ".store", "call")):
            raise RuntimeError("proven scalar was not lowered to register-only Wasm")
        if "i64.store" not in bodies["wide_word"]:
            raise RuntimeError("wide return fixture did not exercise indirect storage")
        read_static = bodies["read_static"]
        if ("memtag.load" in read_static) != profile.mte:
            raise RuntimeError(f"{mode}: unexpected source-static address lowering")
        receipt["modules"][mode] = identity
        for engine in ("int", "aot"):
            vm = [runtime, *profile.uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
                  "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main",
                  "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
            if mode == "plain":
                vm.append("--wasm-feature-disable-memtag-extension")
            run(f"{mode}-{engine}-authorized", [*vm, "--ros-scene-interface", "robot", "abi", "allow", "--run", module])
            run(f"{mode}-{engine}-ungranted", [*vm, "--ros-scene-interface", "robot", "abi", "deny", "--run", module], False)
            if mode == "tagged":
                run(f"{mode}-{engine}-runtime-off", [*vm, "--runtime-disable-memtag", "--ros-scene-interface",
                                                     "robot", "abi", "allow", "--run", module])
    fault_fixture = source.with_name("tagged_access.rs").read_text()
    for delta in (0, 1):
        probe = work / ("probe" + str(delta) + ".rs")
        probe.write_text(fault_fixture.replace("const TAG_DELTA: usize = 1;",
                                              f"const TAG_DELTA: usize = {delta};"))
        binary = work / (probe.stem + ".wasm")
        run("compile-" + probe.stem, [*base[:-2], "-o", binary, "--sysroots", args.sysroots.resolve(), probe])
        for engine in ("int", "aot"):
            vm = [runtime, *Profile(32, exceptions="noeh").uwvm_feature_flags(), "--runtime-" + engine,
                  "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                  "--debug-fault-action", "exit", "--runtime-memtag-backend", "software",
                  "--runtime-memtag-mode", "sync", "--run", binary]
            run(probe.stem + "-" + engine, vm, delta == 0, b"memory tag mismatch" if delta else None)
    stripped = work / "without-debug.wasm"
    without_debug = [arg for arg in base[:-2] if arg != "-g"]
    run("compile-without-debug", [*without_debug, "-o", stripped, "--sysroots", args.sysroots.resolve(), source])
    listing = run("disassemble-without-debug", [tool / "bin/llvm-objdump", "-d", stripped]).decode()
    if "memtag.load" not in wasm_functions(listing)["read_static"]:
        raise RuntimeError("debug option changed source-static tagging")
    sections = run("sections-without-debug", [tool / "bin/llvm-objdump", "-h", stripped]).decode()
    if ".debug_info" in sections:
        raise RuntimeError("release guest retained debug information")
    prior = sha(module)
    for name, flags, error in (("wasm64", ["--target", "wasm64"], b"invalid choice"),
                               ("threads", ["-pthread"], b"unrecognized arguments"),
                               ("eh", ["--eh"], b"panic=abort")):
        run("reject-" + name, [*build, *flags, source], False, error)
    bad = work / "forbidden.rs"
    bad.write_text(source.read_text().replace("unsafe { wros_scene::wr_abi() }", "unsafe { forbidden() }")
                   + '\n#[link(wasm_import_module="unregistered")] unsafe extern "C" { fn forbidden() -> u32; }\n')
    run("reject-import", [*build, bad], False, b"unauthorized import or signature")
    bad.write_text(source.read_text().replace('#[unsafe(export_name = "__wros_no_memtag_state")]',
                                              '#[unsafe(link_section = ".wros.no_memtag")]'))
    run("reject-static-section", [*build, bad], False, b"a Rust static cannot request tag elision")
    bad.write_text("#![feature(core_intrinsics)]\n" + source.read_text())
    run("reject-unstable-feature", [*build, bad], False, b"allow-features")
    if sha(module) != prior:
        raise RuntimeError("a refused build changed the last published Wasm")
    receipt["complete"] = all(sha(Path(p)) == d for p, d in receipt["inputs"].items())
    save()
    if not receipt["complete"]:
        raise RuntimeError("qualification input changed")
    print(len(receipt["cases"]), "Rust frontend cases passed")


if __name__ == "__main__":
    main()
