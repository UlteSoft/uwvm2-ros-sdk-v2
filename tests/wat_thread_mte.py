"""@file wat_thread_mte.py
@brief Qualify the installed WAT assembler with shared memory, a real child and WasmMTE.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys

from platform_projects import digest
from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import sections
from bootstrap import Source, install


def main():
    """@brief Test the default checked build, deterministic tag failure and execution-only opt out."""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--commit", required=True)
    cli.add_argument("--platform", default="unitree")
    for flag in ("vm", "xmake", "output"):
        cli.add_argument("--" + flag, type=Path, required=True)
    args = cli.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = args.output.resolve()
    out.mkdir(mode=0o700)
    vm = args.vm.resolve(strict=True)
    source = Source(args.commit, ROOT)
    sdk = Path(install(source, args.platform, "wat", out / "sdk", [])["directory"])
    project = out / "project"
    shutil.copytree(sdk / "examples/wat/thread-mte", project)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", UWVM_ROS_SDK_ROOT=str(sdk), WROS_PLATFORM=args.platform,
               XMAKE_GLOBALDIR=str(out / "xmake"))
    report = {"complete": False, "commit": args.commit, "platform": args.platform,
              "cgroup": group, "vm_sha256": digest(vm), "checks": {}}

    def run(label, argv, *, denial=None):
        proc = subprocess.run(list(map(str, argv)), cwd=project, env=env, capture_output=True, timeout=90)
        transcript = proc.stdout + proc.stderr
        (out / f"{label}.log").write_bytes(transcript)
        report["checks"][label] = {"exit": proc.returncode, "sha256": hashlib.sha256(transcript).hexdigest()}
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        if denial is None:
            assert proc.returncode == 0, label
        else:
            assert proc.returncode != 0 and denial in transcript, label

    run("configure", [args.xmake, "f", "-p", "wasm-wasip1-threads", "-a", "wasm32", "-y"])
    run("build", [args.xmake, "build", "-j1"])
    guest, = (project / "build").rglob("main.wasm")
    owner, = (project / "build").rglob("owner.wasm")
    receipt = json.loads(guest.with_suffix(".wasm.wros-wat.json").read_bytes())
    assert receipt["mte_requested"] and receipt["authored_tag_writes"] >= 2 and receipt["thread_spawn"]
    assert receipt["shared_memory"] == ["env", "memory"] and not receipt["linear_memory_free"]
    assert ".debug_line" in {name for _, _, name, _ in sections(guest.read_bytes())}
    report["owner_sha256"] = digest(owner)
    report["guest_sha256"] = digest(guest)

    text = (project / "main.wat").read_text()
    point = "    (if (i32.le_s (call $spawn (local.get $address))"
    assert text.count(point) == 1
    stale = out / "stale.wat"
    stale.write_text(text.replace(point, "    (drop (memtag.release $heap (local.get $address) (i32.const 16)))\n" + point))
    stale_wasm = out / "stale.wasm"
    assemble = [sdk / "bin/wrwat", "--threads", "--shared-memory", "env", "memory", "-g"]
    run("assemble-stale", [*assemble, stale, "-o", stale_wasm])
    run("reject-explicit-off", [*assemble, "--no-mte", stale, "-o", out / "refused.wasm"],
        denial=b"WasmMTE")
    run("reject-undeclared-owner", [sdk / "bin/wrwat", "--threads", stale, "-o", out / "refused.wasm"],
        denial=b"unauthorized import or signature env.memory")
    assert not (out / "refused.wasm").exists()

    base = [vm, "-WF3", "-WFE-threads", "--wasi-threads", "3", "3", "1048576", "16777216",
            "2097152", "131072", "--wasm-set-main-module-name", "main", "--runtime-compile-threads", "0",
            "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit",
            "--wasm-preload-library", owner, "env"]
    permission = ["--wasithread-single-create", "main", "--wasithread-single-enable", "main",
                  "--wasithread-single-interface", "main", "thread-spawn", "allow",
                  "--wasithread-single-limit", "main", "max-extra-threads", "1",
                  "--wasithread-single-limit", "main", "max-threads", "2"]
    for engine in ("int", "aot"):
        command = [*base, "--runtime-" + engine, "--runtime-memtag-mode", "sync"]
        run(engine + "-shared-tagged", [*command, *permission, "--run", guest])
        run(engine + "-stale-tag-lifetime", [*command, *permission, "--run", stale_wasm],
            denial=b"memory tag mismatch")
        run(engine + "-runtime-opt-out", [*command, *permission, "--runtime-disable-memtag", "--run", stale_wasm])
        run(engine + "-default-spawn-denied", [*command, "--run", guest], denial=b"thread-spawn")
    report["complete"] = True
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
