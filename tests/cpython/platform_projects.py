"""@file platform_projects.py
@brief Build and run installed Python examples through Xmake's public test interface.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def main():
    """@brief Validate exact final import sets and real per-engine test results for a selected platform."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("installed", "vm", "xmake", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--category", choices=("common", "migration", "extension"), action="append")
    parser.add_argument("--engine", choices=("aot", "int"), action="append")
    a = parser.parse_args()
    root, vm, xmake, output = [p.resolve() for p in (a.installed, a.vm, a.xmake, a.output)]
    platform = root.parents[1].name
    revision = root.parents[2].name
    if root.parent.name != "py" or root.name != "development" or not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("provide a commit-pinned Python development installation")
    output.mkdir()
    sys.path.insert(0, str(root / "install"))
    from imports import inspect
    env = dict(os.environ, PATH="/usr/bin:/bin", TMPDIR=str(output), XMAKE_GLOBALDIR=str(output / "global"),
               WROS_VM=str(vm), UWVM_ROS_SDK_ROOT=str(root), WROS_PLATFORM=platform, PYTHONDONTWRITEBYTECODE="1")
    for var in ("WROS_TOOLCHAIN", "WROS_SYSROOTS", "WROS_RUN_QUERIES"):
        env.pop(var, None)
    def digest(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    results = dict(sdk_commit=revision, platform=platform, vm_sha256=digest(vm), steps=[], modules={})
    def save():
        (output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    def run(name, argv, cwd):
        log = output / (name + ".log")
        start = time.monotonic_ns()
        with log.open("wb") as stream:
            proc = subprocess.run(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=1500)
        results["steps"].append(dict(name=name, elapsed_ns=time.monotonic_ns() - start, exit=proc.returncode,
                                     log_sha256=digest(log)))
        save()
        if proc.returncode:
            raise ValueError(name + ": " + log.read_text(errors="replace")[-1300:])
        return log.read_text(errors="replace")
    operations = {"common": ["abi"], "migration": [],
                  "extension": ["capability.open", "driver.connect", "capability.close"]}
    for area in a.category or operations:
        work = output / area
        shutil.copytree(root / "examples/platform" / platform / area / "py", work)
        run(area + "-configure", [xmake, "f", "-p", "wasm-wasip1", "-a", "wasm32", "-y"], work)
        run(area + "-build", [xmake, "build", "-j1", area], work)
        wasm, = (work / "build").rglob(area + ".wasm")
        actual = sorted((i["module"], i["name"]) for i in inspect(wasm.read_bytes()))
        expected = [("wasi_snapshot_preview1", op) for op in ("clock_time_get", "clock_res_get")]
        expected += [("uwvm_ros_v2", op) for op in operations[area]]
        if actual != sorted(expected):
            raise ValueError("unexpected " + area + " import inventory: " + repr(actual))
        results["modules"][area] = dict(sha256=digest(wasm), imports=actual)
        for engine in a.engine or ("int", "aot"):
            name = area + "/" + engine
            text = run(area + "-" + engine, [xmake, "test", "-j1", name], work)
            text = re.sub(r"\x1b\[[0-9;]*m", "", text)
            report = text.rpartition("report of tests:")[2]
            rows = re.findall(r"^\s*\[ *[0-9]+%\]:\s+(\S+)\s+(\S+)", report, flags=re.M)
            if rows != [(name, "passed")]:
                raise ValueError("xmake did not report the requested passing " + name + " test")
    results["complete"] = True
    save()


if __name__ == "__main__":
    main()
