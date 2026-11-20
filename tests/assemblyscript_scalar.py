#!/usr/bin/env python3
"""@file assemblyscript_scalar.py
@brief Build real AssemblyScript guests from exact selective SDK installations.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

from separate_compilation import cgroup_record, sha
from platform_projects import passed_engines

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import MAX_METADATA, Source, install
from imports import inspect

ABI = {"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}


def main():
    """@brief Build and run each selected common and migration project in INT and AOT."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("xmake", "vm", "wasm-tools", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--platform", action="append")
    args = parser.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    args.output.mkdir(mode=0o700)
    source = Source(args.commit, ROOT)
    registry = json.loads(source.read("share/targets.json", MAX_METADATA))
    platforms = args.platform or list(registry["platforms"])
    results = {"complete": False, "commit": args.commit, "cgroup": group, "platforms": {},
               "inputs": {str(path): sha(path) for path in (args.vm, args.xmake, args.wasm_tools, Path(__file__))}}

    def save():
        temporary = args.output / "pending.json"
        temporary.write_text(json.dumps(results, indent=2) + "\n")
        temporary.replace(args.output / "results.json")

    def run(label, argv, cwd, env, failure=None):
        command = list(map(str, argv))
        p = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=90)
        log = args.output / (label + ".log")
        output = p.stdout + p.stderr
        log.write_bytes(output)
        passed = (p.returncode == 0 if failure is None else p.returncode != 0 and failure in output)
        if not passed:
            raise RuntimeError(f"{label} exited {p.returncode}. See {log}")
        return {"exit": p.returncode, "argv": command, "log_sha256": sha(log)}

    save()
    for index, platform in enumerate(platforms):
        with tempfile.TemporaryDirectory(dir=args.output) as tmp:
            scratch = Path(tmp)
            source.requested.clear()
            record = install(source, platform, "as", scratch / "sdk", [])
            sdk = Path(record["directory"])
            requested = source.requested.copy()
            paths = [path for path in requested if path.startswith("platform/")]
            assert paths and all(path.startswith(f"platform/{platform}/") for path in paths)
            assert all(path.startswith("language/as/") for path in requested if path.startswith("language/"))
            env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(sdk), WROS_VM=str(args.vm),
                       XMAKE_GLOBALDIR=str(scratch / "xmake"))
            checks = {}
            projects = {}
            base = sdk / "examples/platform" / platform
            for area, imports in (("common", [ABI]), ("migration", [])):
                project = base / area / "as"
                prefix = f"{platform}-{area}"
                case = {}
                for label, command in (
                    ("configure", ["f", "-c", "-y"]), ("build", ["build", "-j1"]), ("test", ["test", "-j1"]),
                ):
                    case[label] = run(f"{prefix}-{label}", [args.xmake, *command], project, env)
                artifact, = list((project / "build").rglob("*.wasm"))
                case["validate"] = run(f"{prefix}-validate", [args.wasm_tools, "validate", artifact], project, env)
                output = (args.output / f"{prefix}-test.log").read_text()
                case["engines"] = passed_engines(output, [artifact])
                assert inspect(artifact.read_bytes()) == imports
                case["wasm_sha256"] = sha(artifact)
                projects[area] = case
            if index == 0:
                wras = sdk / "bin/wras"
                plain = scratch / "plain.ts"
                plain.write_text("export function f(x:i32):i32{return x+1;}\n"
                                 "export function _start():void{if(f(41)!=42)unreachable();}\n")
                module = plain.with_suffix(".wasm")
                checks["no_mte"] = run("explicit-no-mte", [wras, plain, "--no-mte", "--build-receipt", "-o", module],
                                       scratch, env)
                proof = json.loads(module.with_suffix(".wasm.wros-as.json").read_bytes())
                assert proof["mte_requested"] is False and proof["linear_memories"] == 0
                checks["no_mte_int"] = run(
                    "explicit-no-mte-int",
                    [args.vm, "-WF3", "-Rint", "--wasm-feature-disable-memtag-extension", "--run", module],
                    scratch, env,
                )
                bad = scratch / "managed.ts"
                bad.write_text("export function f(n:i32):i32 {let a=new Array<i32>(n);a[0]=n;return a[0];}\n"
                               "export function _start():void{}\n")
                reject = scratch / "rejected.wasm"
                checks["managed"] = run("reject-managed", [wras, bad, "-o", reject], scratch, env,
                                        b"requires validated Wasm without linear memory")
                assert not reject.exists()
                checks["unselected_abi"] = run("reject-unselected-abi", [wras, base / "common/as/controller.ts", "-o", reject],
                                              scratch, env, b"must import precisely the selected ROSv2 abi")
                assert not reject.exists()
                common = base / "common/as"
                config = common / "xmake.lua"
                config.write_text(config.read_text().replace("eh = false", "eh = true"))
                checks["unsupported_eh"] = run("reject-eh", [args.xmake, "f", "-c", "-y"], common, env,
                                                b"Core 3.0 without EH")
            results["platforms"][platform] = {"checks": checks, "requested": requested, "projects": projects}
            save()
            print(platform, "common and migration passed in INT/AOT", flush=True)
    results["complete"] = True
    save()


if __name__ == "__main__":
    main()
