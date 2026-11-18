"""Compile a standalone Nim application and exercise its authority and memory on both VM engines."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from separate_compilation import Profile, cgroup_record, inspect, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("producer", "toolchain", "runtime", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--sysroots32", type=Path)
    p.add_argument("--sysroots64", type=Path)
    p.add_argument("--candidate-mte", action="store_true")
    a = p.parse_args()
    if not (a.sysroots32 or a.sysroots64):
        p.error("select at least one width with its sysroot")
    output = a.output.resolve()
    output.mkdir(exist_ok=False, parents=True)
    fixture = ROOT / "tests/nim/scene.nim"
    state = {"cgroup": cgroup_record(), "complete": False, "cases": [], "inputs": {
        str(path): sha(path) for path in (fixture, a.producer, a.toolchain / "bin/clang", a.runtime,
                                        a.sysroots32, a.sysroots64, ROOT / "bin/wrnim",
                                        ROOT / "language/nim/wrnim_lower.nim", ROOT / "language/nim/wros_scene.nim") if path is not None}}
    result = output / "results.json"

    def run(label, argv, expected=None):
        child = subprocess.run(argv, capture_output=True, timeout=120)
        (output / (label + ".stderr")).write_bytes(child.stderr)
        ok = child.returncode == 0 if expected is None else child.returncode != 0 and expected in child.stderr
        state["cases"].append(dict(name=label, code=child.returncode, passed=ok, expected_success=expected is None, argv=list(map(str, argv))))
        result.write_text(json.dumps(state, indent=2))
        if not ok:
            raise RuntimeError(label + ": " + child.stderr.decode(errors="replace")[-1200:])

    base = [sys.executable, ROOT / "bin/wrnim", "--producer", a.producer, "--toolchain", a.toolchain, "-O3", "-g"]
    for width, manifest in ((32, a.sysroots32), (64, a.sysroots64)):
        if manifest is None:
            continue
        binary = output / f"scene{width}.wasm"
        run(f"compile{width}", [*base, "--sysroots", manifest, "--target", f"wasm{width}", "--build-receipt",
                               *(["--legacy-mte"] if a.candidate_mte else []), fixture, "-o", binary])
        names = {(i["module"], i["name"]) for i in inspect(binary.read_bytes())}
        if names != {("uwvm_ros_v2", n) for n in ("abi", "capability.open", "capability.close")}:
            raise ValueError("unexpected guest imports " + repr(names))
        state["inputs"][str(binary)] = sha(binary)
        for engine in ("int", "aot"):
            launch = [a.runtime, *Profile(width).uwvm_feature_flags(), "--runtime-" + engine,
                      "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                      "--wasm-set-main-module-name", "main", "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
            for operation in ("abi", "capability.open", "capability.close"):
                launch += ["--ros-scene-interface", "robot", operation, "allow"]
            run(f"denied{width}-{engine}", [*launch, "--run", binary], b"catch unreachable")
            run(f"allowed{width}-{engine}", [*launch, "--ros-scene-grant", "robot", "signal", "guard", "signal",
                                              "local", "guard.create", "--run", binary])
    state["complete"] = True
    result.write_text(json.dumps(state, indent=2) + "\n")


if __name__ == "__main__":
    main()
