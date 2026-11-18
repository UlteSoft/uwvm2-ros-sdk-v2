"""Compile real Rust no_std source and exercise WasmMTE, source opt-outs and VM grants."""
import argparse
import json
from pathlib import Path
import os
import subprocess

from separate_compilation import Profile, cgroup_record, sha
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("rustroot", "toolchain", "sysroots", "plain-sysroots", "runtime", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--sdk", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    sdk, work, rust, tool, runtime = [p.resolve() for p in
        (args.sdk, args.output, args.rustroot, args.toolchain, args.runtime)]
    source = Path(__file__).with_name("rust") / "core_body.rs"
    receipt = dict(cgroup=cgroup_record(), complete=False, cases=[], modules={})
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    app = sdk / "bin/wrrust"
    inputs = [Path(__file__), source, app, runtime, args.sysroots, args.plain_sysroots,
              rust / "bin/rustc", tool / "bin/clang", sdk / "language/rust/toolchain-inputs.json", sdk / "tools/wasm/tag_ir.cpp"]
    receipt["inputs"] = {str(p): sha(p) for p in inputs}
    report = work / "results.json"

    def save():
        report.write_text(json.dumps(receipt, indent=2) + "\n")

    def run(name, cmd, expected=True, diagnostic=None):
        command = list(map(str, cmd))
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
        if "suppressed" not in suppressions["functions"] or "__wros_no_memtag_state" not in suppressions["globals"]:
            raise RuntimeError("source marked function did not reach the LLVM marker")
        imports = inspect(module.read_bytes())
        if [(r["module"], r["name"]) for r in imports] != [("uwvm_ros_v2", "abi")]:
            raise RuntimeError("unexpected linked imports")
        listing = run("disassemble-" + mode, [tool / "bin/llvm-objdump", "-d", module]).decode()
        for function in ("tagged", "suppressed"):
            body = listing.split(f"<{function}>:", 1)[1].split("\n\n", 1)[0]
            if ("memtag." in body) != (function == "tagged" and mode == "tagged"):
                raise RuntimeError(f"{mode}: incorrect tag operations in {function}")
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
    run("reject-static-section", [*build, bad], False, b"for a Rust static use an export_name")
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
