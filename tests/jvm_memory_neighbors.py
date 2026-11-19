"""Measure live and retired owners in the synchronous TeaVM AOT GC on both VM engines."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import cgroup_record

SDK = Path(__file__).resolve().parents[1]
FIXTURES = SDK / "tests/jvm_memory"
sys.path.insert(0, str(SDK / "install"))
from compiler import compiler_environment
from guest_profile import Profile
from imports import inspect
from private_exports import keep_private_memory


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "sysroots", "java-bundle", "kotlin-bundle", "runtime", "output"):
        parser.add_argument("--" + key, required=True, type=lambda path: Path(path).resolve())
    args = parser.parse_args()
    out = args.output
    out.mkdir(exist_ok=False, parents=True)
    env = dict(PATH=os.defpath, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(out))
    report = dict(complete=False, scope="candidate, wasm32, synchronous single-thread Java and Kotlin GC",
                  cgroup=cgroup_record(), steps=[], modules={}, inputs={})
    for path in (args.toolchain / "bin/clang", args.toolchain / "bin/wasm-ld", args.sysroots, args.runtime,
                 *FIXTURES.iterdir(), Path(__file__), *sorted((SDK / "language/jvm").rglob("*")),
                 *sorted((SDK / "third-parties/jvm").rglob("*"))):
        if path.is_file() and "__pycache__" not in path.parts:
            report["inputs"][str(path)] = sha(path)

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(label, command, expected="pass", environment=env):
        command = list(map(str, command))
        proc = subprocess.run(command, env=environment, capture_output=True, timeout=300)
        log = proc.stdout + proc.stderr
        (out / (label + ".log")).write_bytes(log)
        ok = proc.returncode == 0 if expected == "pass" else proc.returncode != 0 and expected.encode() in log
        report["steps"].append(dict(name=label, argv=command, returncode=proc.returncode, passed=ok))
        save()
        if not ok:
            raise RuntimeError(f"{label}: {log.decode(errors='replace')[-1800:]}")

    save()
    for lang, compiler, ext, bundle in (("java", "wrjava", "java", args.java_bundle),
                                       ("kotlin", "wrkt", "kt", args.kotlin_bundle)):
        directory = out / lang
        directory.mkdir()
        work = directory / "work"
        guest = directory / "application.wasm"
        run(lang + "-compile", [SDK / "bin" / compiler, "--bundle", bundle, "--legacy-mte", "--main-class", "example.Main",
            "--toolchain", args.toolchain, "--sysroots", args.sysroots, "--work", work, FIXTURES / ("Main." + ext), "-o", guest])
        build = json.loads((work / "results.json").read_bytes())
        command = build["steps"][-1]["argv"].copy()
        original = str(SDK / "language/jvm/guest.c")
        if build["steps"][-1]["name"] != "wasm" or command.count(original) != 1:
            raise ValueError("cannot locate exact final TeaVM compile command")
        checked = directory / "observed.wasm"
        command[command.index(original)] = str(FIXTURES / "observe.c")
        command[command.index("-o") + 1] = str(checked)
        run(lang + "-compile-observer", command, environment=compiler_environment(args.toolchain) | {"TMPDIR": str(out)})
        checked.write_bytes(keep_private_memory(checked.read_bytes(), {"_start"}, max_pages=4096))
        for module in (guest, checked):
            if inspect(module.read_bytes()) != [{"module":"uwvm_ros_v2","name":"abi","kind":0,"params":[],"results":["i32"]}]:
                raise ValueError("unexpected managed application import")
            report["modules"][str(module)] = sha(module)
        for engine in ("int", "aot"):
            common = [args.runtime, *Profile().uwvm_feature_flags(), "--runtime-" + engine, "--debug-fault-action", "exit",
                      "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                      "--runtime-memtag-mode", "sync", "--wasm-set-main-module-name", "main"]
            allowed = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                       "--ros-scene-interface", "robot", "abi", "allow"]
            run(lang + "-" + engine + "-hidden", [*common, "--run", guest], "ROS scene interface is hidden")
            for label, flags, module in (("source", [], guest), ("owners", [], checked),
                                        ("owners-disabled", ["--runtime-disable-memtag"], checked)):
                run(lang + "-" + engine + "-" + label, [*common, *allowed, *flags, "--run", module])
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
