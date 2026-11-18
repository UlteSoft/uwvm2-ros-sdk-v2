#!/usr/bin/env python3
"""Install one exact Objective-C selection and run the shipped xmake project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("repository", "toolchain", "objc-clang", "objc-runtime", "sysroots", "vm", "xmake", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    parser.add_argument("--mode", choices=("strict", "candidate", "off"), default="strict")
    options = parser.parse_args()
    group = cgroup_record()
    assert int(group["memory_max"]) == 68719476736 and int(group["swap_max"]) == 0
    out = options.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = Source(options.commit, options.repository.resolve())
    selected = install(source, "unitree", "objectc", out/"installed", [])
    sdk = Path(selected["directory"])
    files = set(source.requested)
    assert {"bin/wrobjc", "language/objectc/xmake/adapter.lua", "platform/unitree/xmake/platform.lua"} <= files
    assert not any(path.startswith("platform/") and not path.startswith("platform/unitree/") for path in files)
    assert not any(path.startswith("language/") and not path.startswith("language/objectc/") for path in files)
    assert not any(path.startswith("third-parties/sources/") for path in files)
    portable = Source(options.commit, options.repository.resolve())
    install(portable, "agilex", "objectc", out/"portable", [])
    assert "platform/agilex/xmake/platform.lua" in portable.requested
    assert "platform/unitree/xmake/platform.lua" not in portable.requested
    skipped = Source(options.commit, options.repository.resolve())
    try:
        install(skipped, "unknown-platform", "objectc", out/"unavailable", [])
    except ValueError as exc:
        assert "unknown platform" in str(exc) and skipped.requested == ["install/revision.py"]
    else:
        raise AssertionError("unknown platform installed")
    demo = out/"project"
    shutil.copytree(sdk/"examples/objectc", demo)
    script = demo/"xmake.lua"
    mode = {"strict": "true", "candidate": '"legacy"', "off": "false"}[options.mode]
    rendered = script.read_text().replace("mte = true", "mte = " + mode)
    assert "mte = " + mode in rendered
    script.write_text(rendered)
    (out/"tmp").mkdir()
    env = dict(os.environ, TMPDIR=str(out/"tmp"), XMAKE_GLOBALDIR=str(out/"xmake-global"),
               UWVM_ROS_SDK_ROOT=str(sdk), WROS_SYSROOTS=str(options.sysroots.resolve()),
               WROS_SYSROOTS_NO_MTE=str(options.sysroots.resolve()), WROS_TOOLCHAIN=str(options.toolchain.resolve()),
               WROS_OBJC_CLANG=str(options.objc_clang.resolve()), WROS_OBJC_RUNTIME=str(options.objc_runtime.resolve()),
               WROS_VM=str(options.vm.resolve()), PYTHONDONTWRITEBYTECODE="1")
    xmake = options.xmake.resolve()
    report = {"complete": False, "commit": options.commit, "requested": sorted(files), "cgroup": group,
              "inputs": {str(p): digest(p) for p in [script, demo/"body.m", options.vm, options.objc_clang,
                                                       options.sysroots, options.objc_runtime/"runtime.json"]}, "cases": []}
    try:
        def run(name, args, allowed, queries=""):
            command = [str(xmake), *args]
            stage = subprocess.run(command, cwd=demo, env=dict(env, WROS_RUN_QUERIES=queries), timeout=120, capture_output=True)
            data = stage.stdout + stage.stderr
            (out/(name+".log")).write_bytes(data)
            ok = stage.returncode == 0 if allowed else stage.returncode != 0 and b"ROS scene interface is hidden" in data
            report["cases"].append({"name": name, "args": command, "queries": queries, "exit": stage.returncode, "passed": ok})
            print(name, stage.returncode, ok, flush=True)
            if not ok:
                raise RuntimeError(data[-2500:].decode(errors="replace"))
        run("configure", ["f", "-P", str(demo), "-c", "-y", "-a", options.target], True)
        run("build", ["-P", str(demo), "-j1", "robot_status"], True)
        guest = next(demo.glob("build/*/"+options.target+"/*/robot_status.wasm"))
        assert guest.read_bytes()[:8] == bytes.fromhex("0061736d01000000")
        report["guest"] = digest(guest)
        run("deny", ["run", "-P", str(demo), "robot_status"], False, "realtime-clock")
        run("allow", ["run", "-P", str(demo), "robot_status"], True, "abi,realtime-clock")
        report["complete"] = True
    finally:
        (out/"results.json").write_text(json.dumps(report, indent=2)+"\n")


if __name__ == "__main__":
    main()
