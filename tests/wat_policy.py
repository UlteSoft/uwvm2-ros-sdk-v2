"""@file wat_policy.py
@brief Verify admitted and rejected core profiles from a selective WAT installation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import sections
from bootstrap import Source, install


def main():
    """@brief Test exact imports, memory, exceptions and thread feature selection."""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--commit", required=True)
    cli.add_argument("--vm", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    args.output.mkdir(mode=0o700)
    results = {}
    env = {key: value for key, value in os.environ.items() if not key.startswith(("WROS_", "UWVM_"))}
    env.update(WROS_VM=str(args.vm.resolve(strict=True)), PATH="/usr/bin:/bin")

    def run(label, argv, *, denial=None):
        proc = subprocess.run(list(map(str, argv)), env=env, capture_output=True, timeout=90)
        transcript = proc.stdout + proc.stderr
        (args.output / (label + ".log")).write_bytes(transcript)
        if denial is None:
            assert proc.returncode == 0, label
        else:
            assert proc.returncode != 0 and denial in transcript, label
        results[label] = {"exit": proc.returncode, "log_sha256": hashlib.sha256(transcript).hexdigest()}

    with tempfile.TemporaryDirectory(dir=args.output) as directory:
        work = Path(directory)
        source = Source(args.commit, ROOT)
        sdk = Path(install(source, "unitree", "wat", work / "sdk", [])["directory"])
        assert all(path.startswith("language/wat/") for path in source.requested if path.startswith("language/"))
        assert all(path.startswith("platform/unitree/") for path in source.requested if path.startswith("platform/"))
        assembler = sdk / "bin/wrwat"
        module = work / "test.wasm"
        text = work / "input.wat"
        empty = '(module (func (export "_start")))'
        abi = '(module (import "uwvm_ros_v2" "abi" (func (result i32))))'
        wrong_abi = '(module (import "uwvm_ros_v2" "abi" (func (result i64))))'
        eh = '''(module
          (tag $error (param i32))
          (func (export "_start")
            (i32.ne
              (block $caught (result i32)
                (try_table (catch $error $caught) (throw $error (i32.const 73)))
                unreachable)
              (i32.const 73))
            if unreachable end))'''
        mem64 = '''(module (memory i64 1 1)
          (func (export "_start")
            (i32.store (i64.const 16) (i32.const 123))
            (if (i32.ne (i32.load (i64.const 16)) (i32.const 123)) (then unreachable))))'''
        atomics = '''(module (memory 1 1 shared)
          (func (export "_start")
            (i32.atomic.store (i32.const 0) (i32.const 81))
            (if (i32.ne (i32.atomic.load (i32.const 0)) (i32.const 81)) (then unreachable))))'''

        def build(label, wat, *flags, denial=None):
            text.write_bytes(wat if isinstance(wat, bytes) else wat.encode())
            module.unlink(missing_ok=True)
            run(label, [assembler, text, "-o", module, *flags], denial=denial)
            assert module.exists() == (denial is None), label
            return module.read_bytes() if denial is None else None

        runner = sdk / "tools/xmake/run_guest.py"

        def execute(label, arch="wasm32", core="3.0", eh_mode="eh", thread_mode="single", mte=True):
            for engine in ("int", "aot"):
                run(label + "-" + engine, [sys.executable, runner, module, arch, core, thread_mode,
                                          "--engine", engine, "--exceptions", eh_mode,
                                          "--check-tags" if mte else "--disable-tags"])

        debug = build("mvp", empty, "--core", "mvp", "-g", "--build-receipt")
        assert ".debug_line" in {name for _, _, name, _ in sections(debug)}
        receipt = json.loads(module.with_suffix(".wasm.wros-wat.json").read_bytes())
        assert receipt["linear_memory_free"] and receipt["mte_requested"]
        assert receipt["wasm_sha256"] == hashlib.sha256(debug).hexdigest()
        execute("mvp", core="mvp", eh_mode="noeh")
        assert debug == build("mvp-no-mte", empty, "--core", "mvp", "-g", "--no-mte")
        assert not module.with_suffix(".wasm.wros-wat.json").exists()
        build("eh", eh)
        execute("eh")
        build("memory64", mem64, "--target", "wasm64", "--no-mte")
        execute("memory64", "wasm64", mte=False)
        build("threads", atomics, "--threads", "--no-mte")
        execute("threads", thread_mode="threads", mte=False)

        build("reject-memory", mem64, "--target", "wasm64", denial=b"default MTE requires no linear memory")
        build("reject-memory64", mem64, "--no-mte", denial=b"memory64")
        build("reject-threads", atomics, "--no-mte", denial=b"threads")
        build("reject-eh", eh, "--no-eh", denial=b"exceptions")
        build("reject-mvp-eh", empty, "--core", "mvp", "--eh", denial=b"MVP requires")
        build("reject-unselected", abi, denial=b"unauthorized import or signature")
        build("reject-signature", wrong_abi, "--ros-operation", "abi", denial=b"unauthorized import or signature")
        build("reject-missing", empty, "--ros-operation", "abi", denial=b"must import each selected")
        build("reject-unknown", empty, "--ros-operation", "absent", denial=b"select distinct operations")
        build("reject-component", "(component)", denial=b"Component Model binaries")
        build("reject-wasip1", '(module (import "wasi_snapshot_preview1" "clock_time_get" (func)))',
              denial=b"unauthorized import or signature")
        build("reject-wasip2", '(module (import "wasi:io/poll@0.2.0" "poll" (func)))',
              denial=b"P2/P3")
        build("reject-wasip3", '(module (import "wasi_snapshot_preview3" "run" (func)))',
              denial=b"P2/P3")
        build("reject-binary", debug, denial=b"expects text input")
        build("reject-invalid", '(module (func (result i32) nop))', denial=b"type mismatch")
        build("preserve-artifact", empty)
        previous = module.read_bytes()
        text.write_text("(invalid)")
        run("reject-preserve", [assembler, text, "-o", module], denial=b"error")
        assert module.read_bytes() == previous
    report = {"complete": True, "commit": args.commit, "cgroup": group, "checks": results}
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
