"""Check mutable Fortran metadata and address transmission over the real ROS ABI."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import Profile, ROOT, cgroup_record, inspect, sha, candidate_arguments, candidate_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "flang", "sysroots", "plain-sysroots", "runtime", "output"):
        parser.add_argument("--" + key, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--host-cxx", type=Path, default=Path("/usr/bin/c++"))
    candidate_arguments(parser)
    args = parser.parse_args()
    work = args.output
    state = {"complete": False, "cgroup": cgroup_record(), "cases": [], "modules": {}}
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    (work / "results.json").write_text(json.dumps(state))
    fixture = ROOT / "tests/fortran"
    marker = work / "wros-flang-mte"
    language = ROOT / "language/fortran"
    inputs = (args.toolchain / "bin/clang", args.flang, args.sysroots, args.plain_sysroots, args.runtime,
              language / "mark_mte.cpp", language / "frontend_fortran.py", fixture / "address.f90", fixture / "address.c", Path(__file__))
    state["inputs"] = {str(path): sha(path) for path in inputs}

    def save():
        (work / "results.json").write_text(json.dumps(state, indent=2) + "\n")

    def run(label, cmd, error=None):
        command = candidate_command(cmd, args.candidate_mte)
        proc = subprocess.run(command, cwd=work, capture_output=True, timeout=120)
        (work / (label + ".stderr")).write_bytes(proc.stderr)
        state["cases"].append(dict(name=label, argv=command, exit=proc.returncode, expected_error=error))
        save()
        if (proc.returncode == 0) != (error is None) or (error and error.encode() not in proc.stderr):
            raise RuntimeError(label + ": " + proc.stderr[-1000:].decode(errors="replace"))
        return proc.stdout

    run("prepare-marker", [sys.executable, language / "prepare.py", "--toolchain", args.toolchain,
                           "--host-cxx", args.host_cxx.absolute(), "--output", marker])
    for width in (32, 64):
        ir = work / f"metadata-{width}.ll"
        ir.write_text(f'target datalayout = "e-p:{width}:{width}"\ntarget triple = "wasm{width}-unknown-wasip1"\n'
                      '@ordinary = global i32 0\n@dynamic = global i32 0, sanitize_address_dyninit\n'
                      '@asan = global i32 0, no_sanitize_address\n@hwasan = global i32 0, no_sanitize_hwaddress\n'
                      '@disabled = global i32 0, no_sanitize_address, no_sanitize_hwaddress\n')
        for mode, sysroots in (("on", args.sysroots), ("off", args.plain_sysroots)):
            name = f"wasm{width}-{mode}"
            bc = work / (name + ".bc")
            run(name + "-mark", [marker, width, mode, ir, bc])
            decoded = run(name + "-inspect", [args.toolchain / "bin/llvm-dis", bc, "-o", "-"]).decode()
            for symbol in ("ordinary", "dynamic", "asan", "hwasan", "disabled"):
                row = next(line for line in decoded.splitlines() if line.startswith("@" + symbol + " = "))
                if ("sanitize_memtag" in row) != (mode == "on" and symbol != "disabled"):
                    raise RuntimeError(name + " incorrect metadata: " + row)
                if symbol != "ordinary" and "sanitize_" not in row:
                    raise RuntimeError(name + " lost existing metadata: " + row)
            profile = Profile(width, mte=mode == "on", exceptions="noeh")
            flags = ["--target", f"wasm{width}", "--toolchain", args.toolchain, "--sysroots", sysroots,
                     "--no-eh", "--mte" if mode == "on" else "--no-mte", "-O3", "-g"]
            obj = work / (name + ".o")
            module = work / (name + ".wasm")
            run(name + "-c", [ROOT / "bin/wrc", *flags, "-c", fixture / "address.c", "-o", obj])
            run(name + "-fortran", [ROOT / "bin/wrf", *flags, "--flang", args.flang, "--mte-tool", marker,
                                    fixture / "address.f90", "--link-object", obj, "-o", module])
            imports = inspect(module.read_bytes())
            if sorted((i["module"], i["name"]) for i in imports) != [
                ("uwvm_ros_v2", "capability.close"), ("uwvm_ros_v2", "capability.open")]:
                raise RuntimeError("unexpected final import surface")
            state["modules"][name] = {"sha256": sha(module), "imports": imports}
            for engine in ("int", "aot"):
                launch = [args.runtime, *profile.uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
                          "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main",
                          "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
                if mode == "off":
                    launch.append("--wasm-feature-disable-memtag-extension")
                for op in ("capability.open", "capability.close"):
                    launch.extend(["--ros-scene-interface", "robot", op, "allow"])
                run(name + "-" + engine + "-denied", [*launch, "--run", module], "catch unreachable")
                run(name + "-" + engine, [*launch, "--ros-scene-grant", "robot", "signal", "guard", "signal", "local",
                                          "guard.create", "--run", module])
    state["complete"] = all(sha(Path(path)) == digest for path, digest in state["inputs"].items())
    save()
    if not state["complete"]:
        raise RuntimeError("a recorded qualification input changed")


if __name__ == "__main__":
    main()
