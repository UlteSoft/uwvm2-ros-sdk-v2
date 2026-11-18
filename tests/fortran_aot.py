"""Compile Fortran to Wasm, verify actual MTE in its own code and run both VM engines."""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
from separate_compilation import Profile, cgroup_record, inspect, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "flang", "mte-tool", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--sysroots", required=True, action="append", type=Path)
    parser.add_argument("--no-mte", action="store_true", help="exercise the complete untagged profile")
    opt = parser.parse_args()
    tc, fc, marker, vm, work = (p.resolve() for p in
        (opt.toolchain, opt.flang, opt.mte_tool, opt.runtime, opt.output))
    receipts = [p.resolve() for p in opt.sysroots]
    state = dict(complete=False, cgroup=cgroup_record(), cases=[], modules={})
    work.mkdir(parents=True, exist_ok=False)
    (work / "tmp").mkdir()
    os.environ["TMPDIR"] = str(work / "tmp")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    fixtures = ROOT / "tests/fortran"
    inputs = [tc / "bin/clang", tc / "bin/wasm-ld", tc / "bin/llvm-objdump", *receipts, fc, marker,
              marker.with_name(marker.name + ".json"), vm, ROOT / "bin/wrfortran", ROOT / "bin/wrc",
              ROOT / "share/abi/ros.json", Path(__file__), *fixtures.glob("*"),
              *(ROOT / "language/fortran").glob("*.py"), *(ROOT / "language/fortran").glob("*.cpp"),
              ROOT / "language/fortran/entry.c", *(ROOT / "install").glob("*.py"),
              *(p for p in (ROOT / "third-parties/fortran").rglob("*") if p.is_file())]
    state["inputs"] = {str(p): sha(p) for p in inputs}

    def save():
        (work / "results.json").write_text(json.dumps(state, indent=2) + "\n")

    def run(name, argv, error=None):
        argv = list(map(str, argv))
        process = subprocess.run(argv, cwd=work, capture_output=True, timeout=180)
        (work / (name + ".stderr")).write_bytes(process.stderr)
        (work / (name + ".stdout")).write_bytes(process.stdout)
        state["cases"].append(dict(name=name, argv=argv, code=process.returncode, expected_error=error))
        save()
        if (process.returncode != 0) != (error is not None) or (error and error.encode() not in process.stderr):
            raise RuntimeError(f"{name}: " + process.stderr.decode(errors="replace")[-2000:])
        print(name, process.returncode, flush=True)
        return process.stdout

    missing = work / "missing.f90"
    missing.write_text("program broken\nuse missing_module\nend program\n")
    suppressed = work / "suppressed.ll"
    suppressed.write_text('target datalayout = "e-p:32:32"\ntarget triple = "wasm32-unknown-wasip1"\n'
                          'define void @bad() disable_sanitizer_instrumentation { ret void }\n')
    bitcode = work / "attribute.bc"
    run("marker-retains-attribute", [marker, 32, "on", suppressed, bitcode])
    decoded = run("inspect-attribute", [tc / "bin/llvm-dis", bitcode, "-o", "-"])
    if b"disable_sanitizer_instrumentation" not in decoded or b"sanitize_memtag" in decoded:
        raise RuntimeError("marker overrode an explicit LLVM sanitizer attribute")
    for bits in (32, 64):
        for eh in ("eh", "noeh"):
            name = f"wasm{bits}-{eh}"
            profile = Profile(bits, exceptions=eh, mte=not opt.no_mte)
            flags = ["--toolchain", tc, *(arg for receipt in receipts for arg in ("--sysroots", receipt)), "--target", f"wasm{bits}",
                     "--eh" if eh == "eh" else "--no-eh", "-O3", "-g"]
            if opt.no_mte:
                flags.append("--no-mte")
            cmd = [sys.executable, ROOT / "bin/wrfortran", *flags, "--flang", fc, "--mte-tool", marker]
            output, obj = work / (name + ".wasm"), work / (name + ".o")
            run(name + "-compile-c", [sys.executable, ROOT / "bin/wrc", *flags, fixtures / "interop.c",
                                      "-c", "-o", obj])
            run(name + "-compile-fortran", [*cmd, fixtures / "body.f90", "--link-object", obj, "-o", output])
            imports = inspect(output.read_bytes())
            if imports != [dict(module="uwvm_ros_v2", name="abi", kind=0, params=[], results=["i32"])]:
                raise RuntimeError(f"{name}: final imports changed: {imports}")
            assembly = run(name + "-disassemble", [tc / "bin/llvm-objdump", "-d", "--mattr=+memtag", output])
            # Inspect _QQmain. Instructions originating from the C fixture or linker do not count.
            body = re.search(rb"<_QQmain>:(.*?)(?:\n[0-9a-f]+ <|\Z)", assembly, re.S)
            if b"<_FortranAExponent8_4>" not in assembly:
                raise RuntimeError(name + ": missing upstream numeric runtime procedure")
            if not body:
                raise RuntimeError(name + ": missing Fortran function")
            if opt.no_mte:
                if b"memtag." in assembly:
                    raise RuntimeError(name + ": MTE instruction in plain target")
            elif (b"memtag.random" not in body.group(1) or body.group(1).count(b"memtag.hintstore") < 2
                  or body.group(1).count(b"memtag.store") < 2):
                raise RuntimeError(name + ": required Fortran stack-tagging instructions missing")
            identity = sha(output)
            state["modules"][name] = dict(sha256=identity, imports=imports,
                                          verified_function="_QQmain", profile=profile.to_dict())
            for engine in ("int", "aot"):
                start = [vm, *profile.uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads",
                         "0", "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main"]
                run(name + "-hidden-" + engine, [*start, "--run", output], "ROS scene interface is hidden")
                run(name + "-" + engine, [*start, "--ros-scene-create", "robot", "--ros-scene-bind", "robot",
                    "main", "--ros-scene-interface", "robot", "abi", "allow", "--run", output])
            if len(receipts) > 1:
                run(name + "-mixed-refused", [*cmd, "--mte" if opt.no_mte else "--no-mte",
                    fixtures / "body.f90", "--link-object", obj, "-o", output], "guest profile mismatch")
            run(name + "-module-refused", [*cmd, missing, "-o", output], "missing_module")
            if sha(output) != identity:
                raise RuntimeError("failed compilation replaced a previously published executable")

    if any(sha(Path(p)) != expected for p, expected in state["inputs"].items()):
        raise RuntimeError("qualification inputs changed")
    state["complete"] = True
    save()


if __name__ == "__main__":
    main()
