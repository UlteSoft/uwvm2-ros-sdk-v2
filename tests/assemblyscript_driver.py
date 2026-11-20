"""@file assemblyscript_driver.py
@brief Test exact AssemblyScript imports, private staging, and live VM permission checks.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from separate_compilation import cgroup_record, sha

ROOT = Path(__file__).resolve().parents[1]
OPEN = "capability.open"
CLOSE = "capability.close"
CONNECT = "driver.connect"
XMAKE = '''
set_project("assemblyscript-driver")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("driver")
    set_kind("binary")
    set_language("as")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", eh = false, mte = true, build_receipt = true})
    set_symbols("debug")
    add_wros_operations("capability.open", "capability.close", "driver.connect")
    set_wros_test_policy("platform-driver-denial")
    add_files("controller.ts")
    add_wros_tests("int", "aot")
target_end()
'''
READ_ONLY = """
import { open, opened, close, writeWord, setRequestWipe, clearRequest, replySize, replyRequired } from "./wros";

export function _start(): void {
    writeWord(0, 0x6461757267); // Starts with an absent alias, not the granted one.
    if (open(5) != 13 || opened() != 0) unreachable();
    writeWord(0, 0x6472617567); // "guard"
    if (open(5) != 0 || opened() == 0 || close(opened()) != 0 || opened() != 0) unreachable();
    if (open(5) != 22 || opened() != 0) unreachable();
    setRequestWipe(false);
    writeWord(0, 0x6472617567);
    if (open(5) != 0 || close(opened()) != 0 || opened() != 0) unreachable();
    if (open(5) != 0 || close(opened()) != 0 || opened() != 0) unreachable();
    clearRequest();
    if (open(5) != 22 || opened() != 0 || replySize() != 0 || replyRequired() != 0) unreachable();
}
"""
DENIED = """
import { open, opened, close, connect, writeWord, replySize, replyRequired, clearReply } from "./wros";

export function _start(): void {
    writeWord(0, 0x6472617567); // "guard"
    if (open(5) != 0 || opened() == 0) unreachable();
    if (connect(opened()) != 13 || replySize() != 0 || replyRequired() != 0) unreachable();
    clearReply();
    if (close(opened()) != 0 || opened() != 0) unreachable();
}
"""


def source_function(binding, body):
    """@brief Construct a single-operation boundary assertion."""
    return (f'import {{ {binding} }} from "./wros";\n'
            f'export function _start(): void {{ {body} }}\n')


def main():
    """@brief Execute both VM engines on an exact selectively installed wras."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--vm", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--output", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--xmake", type=lambda value: Path(value).resolve())
    args = parser.parse_args()
    if not __debug__:
        parser.error("qualification requires Python assertions")
    group = cgroup_record()
    args.output.mkdir(mode=0o700)
    evidence = {"complete": False, "cgroup": group, "vm_sha256": sha(args.vm),
                "sdk_commit": args.commit, "cases": {}}

    def save():
        temporary = args.output / "results.pending"
        temporary.write_text(json.dumps(evidence, indent=2) + "\n")
        temporary.replace(args.output / "results.json")

    with tempfile.TemporaryDirectory(dir=args.output) as work:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "XMAKE_"))}
        env.update(TMPDIR=work, PYTHONDONTWRITEBYTECODE="1")

        def run(label, command, expected=0, message=None, cwd=None):
            result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, timeout=180)
            log = args.output / (label + ".log")
            log.write_bytes(result.stdout + result.stderr)
            evidence["cases"][label] = {"exit": result.returncode, "log_sha256": sha(log)}
            save()
            assert result.returncode == expected, (label, result.stderr[-1024:])
            assert message is None or message in result.stderr, (label, result.stderr[-1024:])
            return result.stdout

        out = run("install", [sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
                  "--local-repository", ROOT, "--commit", args.commit, "--platform", "unitree",
                  "--language", "as", "--prefix", work, "--", "--component", "development"])
        selected = json.loads(out)
        sdk = Path(selected["directory"])
        evidence["sdk_commit"] = selected["commit"]
        frontend = [sdk / "bin/wras", "--ros-driver", "--build-receipt", "-g"]

        def build(label, source, ops=(), extra=(), expected=0, message=None):
            app = args.output / (label + ".ts")
            artifact = app.with_suffix(".wasm")
            app.write_text(source)
            flags = [arg for name in ops for arg in ("--ros-operation", name)]
            run(label + "-build", [*frontend, *extra, *flags, app, "-o", artifact], expected, message)
            assert artifact.is_file() == (expected == 0)
            assert artifact.with_suffix(".wasm.wros-as.json").is_file() == (expected == 0)
            if expected == 0:
                evidence["cases"][label + "-build"]["wasm_sha256"] = sha(artifact)
            return artifact

        def vm(label, artifact, ops, *, plain=False, runtime_off=False, trap=False):
            config = ["--wasm-set-main-module-name", "main", "--wasip1-single-create", "main",
                      "--wasip1-single-disable", "main", "--ros-scene-create", "robot",
                      "--ros-scene-bind", "robot", "main",
                      "--ros-scene-grant", "robot", "guard", "guard", "signal", "local", "guard.create"]
            for op in ops:
                config.extend(["--ros-scene-interface", "robot", op, "allow"])
            mte = (["--wasm-feature-disable-memtag-extension"] if plain else
                   ["--runtime-disable-memtag"] if runtime_off else ["--runtime-memtag-mode", "sync"])
            for engine in ("int", "aot"):
                run(label + "-" + engine, [args.vm, "-WF3", "--runtime-" + engine, "--runtime-compile-threads", "0",
                    "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit",
                    *mte, *config, "--run", artifact], 120 if trap else 0, b"unreachable" if trap else None)

        for plain in (False, True):
            label = "staging-plain" if plain else "staging-tagged"
            binary = build(label, READ_ONLY, (OPEN, CLOSE), ("--no-mte",) if plain else ())
            vm(label, binary, (OPEN, CLOSE), plain=plain)
            if not plain:
                vm("staging-runtime-off", binary, (OPEN, CLOSE), runtime_off=True)
        denied = build("denied-purpose", DENIED, (OPEN, CLOSE, CONNECT))
        vm("denied-purpose", denied, (OPEN, CLOSE, CONNECT))
        for label, source, ops in [
            ("write-byte-limit", source_function("writeByte", "writeByte(512, 1);"), ()),
            ("write-byte-value", source_function("writeByte", "writeByte(0, 256);"), ()),
            ("write-word-edge", source_function("writeWord", "writeWord(505, 1);"), ()),
            ("read-invalid", source_function("readWord", "if (readWord(4294967295) != 0) unreachable();"), ()),
            ("submit-limit", source_function("submit", "if (submit(0, 513) != 0) unreachable();"), ("driver.submit",)),
        ]:
            artifact = build(label, source, ops)
            vm(label, artifact, ops, trap=True)
        build("unrequested-import", DENIED, (OPEN, CLOSE), expected=1, message=b"differ from the requested operations")
        build("unknown-module", """
@external("wasi_snapshot_preview1", "fd_close")
declare function native(fd: i32): i32;
export function _start(): void { if (native(0) != 0) unreachable(); }
""", expected=1, message=b"requires only the SDK driver declarations")
        build("raw-memory", """
import { writeWord } from "./wros";
export function _start(): void { store<u8>(0, 42); writeWord(0, 0); }
""", expected=1, message=b"requires validated Wasm without linear memory")
        if args.xmake:
            project = Path(work) / "xmake-driver"
            project.mkdir()
            (project / "xmake.lua").write_text(XMAKE)
            (project / "controller.ts").write_text(DENIED.replace("0x6472617567", "0x6d7261").replace("open(5)", "open(3)"))
            env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_VM=str(args.vm), XMAKE_GLOBALDIR=str(Path(work) / "config"))
            for label, command in (("configure", ["f", "-c", "-y"]), ("build", ["build", "-j1"]), ("test", ["test", "-j1"])):
                run("xmake-" + label, [args.xmake, *command, "-P", str(project)], cwd=project)
    evidence["complete"] = True
    save()


if __name__ == "__main__":
    main()
