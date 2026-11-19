"""Build installed C and F# migration projects and check both real VM test engines."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install
from imports import inspect
sys.path.insert(0, str(ROOT / "tests"))
from platform_projects import passed_engines


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(log, args, cwd, env, success=True):
    """@brief Preserve process output and distinguish an application trap from a harness failure."""
    with log.open("wb") as stream:
        result = subprocess.run(args, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=240, check=False)
    text = log.read_text(errors="replace")
    if (result.returncode == 0) != success:
        raise ValueError(f"{log}: exit {result.returncode}\n{text[-3000:]}")
    return text


def qualify(args, platform, language, roots):
    """@brief Install a single immutable selection and exercise its public Xmake project."""
    case = args.output / (platform + "-" + language)
    case.mkdir(exist_ok=False)
    selection = install(Source(args.commit, ROOT), platform, language, args.output / "installs",
                        ["--component", "migration"], site_profile=args.c_site if language == "c" else None)
    sdk = Path(selection["directory"])
    selected = Path("examples/platform") / platform / "migration" / language
    inventory = {p.relative_to(sdk / "examples/platform") for p in (sdk / "examples/platform").rglob("xmake.lua")}
    required = Path(platform, "migration", language, "xmake.lua")
    if required not in inventory or any(len(p.parts) < 4 or p.parts[0] != platform or p.parts[2] != language for p in inventory):
        raise ValueError("missing selected project or unexpected platform/language in the installation")
    project = case / "project"
    shutil.copytree(sdk / selected, project)
    env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(sdk), WROS_VM=str(args.vm),
               WROS_RUN_QUERIES="abi" if language == "fsharp" else "", PYTHONDONTWRITEBYTECODE="1")
    env.pop("WROS_ROS_PACKAGE_ROOT", None)
    if language == "c":
        for name in ("WROS_SYSROOTS", "WROS_TOOLCHAIN", "WROS_SYSROOTS_NO_MTE"):
            env.pop(name, None)
        if platform in roots:
            env["WROS_ROS_PACKAGE_ROOT"] = str(roots[platform])
    run(case / "configure.log", [args.xmake, "f", "-c", "-y", "-a", "wasm32"], project, env)
    run(case / "build.log", [args.xmake, "-j1"], project, env)
    log = run(case / "run.log", [args.xmake, "test", "-j1", "-v"], project, env)
    target, = (project / "build").rglob("*.wasm")
    engines = passed_engines(log, [target])
    imports = inspect(target.read_bytes())
    expected = [("uwvm_ros_v2", "abi")] if language == "fsharp" else []
    if [(row["module"], row["name"]) for row in imports] != expected:
        raise ValueError("unexpected module imports")
    record = {"platform": platform, "language": language, "site": selection.get("site_release_sha256"),
              "sha256": sha(target), "bytes": target.stat().st_size, "imports": imports,
              "build": sha(case / "build.log"), "tests": sha(case / "run.log"), "engines": engines}
    if language == "c":
        pin = project / "upstream.lock" if platform in roots else sdk / "examples/shared/migration/c/imu.lock"
        record.update(input=json.loads(pin.read_bytes())[0], origin="local-package" if platform in roots else "bundled")
    else:
        # Repeat the real executable in the closed VM. No host query is available.
        closed = dict(env, WROS_RUN_QUERIES="")
        record["denials"] = {}
        for engine in ("int", "aot"):
            receipt = case / (engine + "-closed.log")
            log = run(receipt, [sys.executable, sdk / "tools/xmake/run_guest.py", target,
                      "wasm32", "3.0", "single", "--engine", engine, "--check-tags", "--exceptions", "eh"],
                      project, closed, False)
            if "scene interface is hidden" not in log:
                raise ValueError("unexpected closed VM diagnostic: " + log[-1200:])
            record["denials"][engine] = sha(receipt)
    return record


def controls(args, case):
    """@brief Verify that changed ROS bytes and an incorrect F# assertion both fail."""
    base = args.output / "controls"
    base.mkdir()
    platform = case["platform"]
    fs = args.output / "installs" / args.commit / platform / "fsharp/migration"
    cs = args.output / "installs" / args.commit / platform / "c/migration"
    package = base / "sensor_msgs"
    shutil.copytree(cs / "third-parties/migration-examples/sensor_msgs", package)
    resource = package / "msg/Imu.msg"
    resource.write_bytes(resource.read_bytes() + b"\n")
    prepare = cs / "examples/shared/migration/c/prepare.py"
    out = base / "pack"
    log = run(base / "changed.log", [sys.executable, "-I", "-B", prepare, "--package-root", package,
              "--platform-lock", prepare.with_name("imu.lock"), "--output", out], base, os.environ, False)
    if "does not match its lock" not in log or out.exists():
        raise ValueError("a changed resource was not rejected before output")
    text = (fs / "examples/shared/migration/fsharp/GoalStatus.fs").read_text()
    if text.count("mask = 828") != 1:
        raise ValueError("the negative control must mutate exactly one expected terminal mask")
    source = base / "GoalStatus.fs"
    source.write_text(text.replace("mask = 828", "mask = 829"))
    bad = base / "wrong-expectation.wasm"
    run(base / "fsharp-build.log", [fs / "bin/wrfs", "--dotnet", os.environ["WROS_DOTNET"],
        "--mono-compiler", os.environ["WROS_MONO"], "--toolchain", os.environ["WROS_TOOLCHAIN"],
        "--scene-entry", "GoalStatus.Start", source, "-o", bad], base, os.environ)
    for engine in ("int", "aot"):
        log = run(base / (engine + "-assert.log"), [sys.executable, fs / "tools/xmake/run_guest.py",
                  bad, "wasm32", "3.0", "single", "--engine", engine, "--check-tags", "--exceptions", "eh"],
                  base, dict(os.environ, WROS_VM=str(args.vm), WROS_RUN_QUERIES="abi"), False)
        if "unreachable" not in log.lower() and "trap" not in log.lower():
            raise ValueError("invalid F# assertion did not trap: " + log[-750:])
    return {"changed_resource_rejected": sha(base / "changed.log"),
            "fsharp_wrong_mask_traps": {e: sha(base / (e + "-assert.log")) for e in ("int", "aot")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--platform", action="append")
    parser.add_argument("--language", choices=("c", "fsharp"), action="append")
    parser.add_argument("--vm", type=Path, required=True)
    parser.add_argument("--xmake", type=Path, required=True)
    parser.add_argument("--c-site", type=Path)
    parser.add_argument("--package-roots", type=Path, help="local JSON map from platform to unpacked ROS package directory")
    parser.add_argument("--controls", action="store_true", help="also run mutation tests using both installations")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    cg = Path("/proc/self/cgroup").read_text()
    route = next(line[3:] for line in cg.splitlines() if line.startswith("0::"))
    memory = Path("/sys/fs/cgroup") / route.lstrip("/")
    if (memory.joinpath("memory.max").read_text().strip() != str(64 << 30)
            or memory.joinpath("memory.swap.max").read_text().strip() != "0"):
        parser.error("the qualification requires an existing 64 GiB memory cgroup with swap disabled")
    if not re.fullmatch("[0-9a-f]{40}", args.commit):
        parser.error("supply the full immutable SDK commit")
    platforms = json.loads((ROOT / "share/targets.json").read_bytes())["platforms"]
    selected = args.platform or sorted(platforms)
    if not set(selected) <= set(platforms):
        parser.error("unknown platform")
    roots = json.loads(args.package_roots.read_bytes()) if args.package_roots else {}
    report = {"commit": args.commit, "vm": sha(args.vm), "cgroup": route, "cases": [], "complete": False}
    try:
        for name in selected:
            for language in args.language or ("c", "fsharp"):
                report["cases"].append(qualify(args, name, language, roots))
                print(name, language, flush=True)
        if args.controls:
            report["controls"] = controls(args, report["cases"][0])
        report["complete"] = True
    finally:
        (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
