"""@file managed_platforms.py
@brief Build real installed .NET platform projects and run both VM engines serially.
"""
import argparse
import json
import os
from pathlib import Path
import shutil

from platform_examples import ROOT, Source, install, inspect, run, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--vm", type=Path, required=True)
    parser.add_argument("--xmake", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = Path("/sys/fs/cgroup") / next(line[3:].lstrip("/") for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    if (current.joinpath("memory.max").read_text().strip(), current.joinpath("memory.swap.max").read_text().strip()) != (str(64 << 30), "0"):
        parser.error("use an existing 64 GiB cgroup with swap disabled")
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    report = {"complete": False, "commit": args.commit, "vm": sha(args.vm), "cgroup": str(current), "cases": []}
    try:
        for language in ("fsharp", "csharp", "vbnet"):
            result = install(Source(args.commit, ROOT), args.platform, language, out / "installs", ["--component", "migration"])
            sdk = Path(result["directory"])
            inventory = [p.relative_to(sdk / "examples/platform") for p in (sdk / "examples/platform").rglob("xmake.lua")]
            if any(len(p.parts) < 4 or p.parts[0] != args.platform or p.parts[2] != language for p in inventory):
                raise ValueError("installation included another platform or language")
            for area in (("extension",) if language == "fsharp" else ("migration", "extension")):
                case = out / (language + "-" + area)
                case.mkdir()
                project = case / "src"
                shutil.copytree(sdk / "examples/platform" / args.platform / area / language, project)
                env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(sdk), WROS_VM=str(args.vm), WROS_RUN_QUERIES="")
                run(case / "configure.log", [args.xmake, "f", "-c", "-y", "-a", "wasm32"], project, env)
                # Xmake's test action builds the target before dispatching the two VM invocations.
                log = run(case / "execute.log", [args.xmake, "test", "-j1", "-v"], project, env)
                if not all("--engine " + e in log for e in ("int", "aot")) or "tests passed" not in log:
                    raise ValueError("missing VM dispatch or test result")
                target, = (project / "build").rglob("*.wasm")
                imports = [(row["module"], row["name"]) for row in inspect(target.read_bytes())]
                expected = (["capability.open", "driver.connect", "driver.disconnect", "capability.close"]
                            if area == "extension" else ["abi"])
                if imports != [("uwvm_ros_v2", op) for op in expected]:
                    raise ValueError("unexpected final import set")
                if area == "extension" and "--driver-denial " + args.platform not in log:
                    raise ValueError("missing platform driver permission fixture")
                report["cases"].append(dict(platform=args.platform, language=language, area=area,
                       sha256=sha(target), bytes=target.stat().st_size, imports=imports,
                       engines=["int", "aot"], transcript=sha(case / "execute.log")))
                print(args.platform, language, area, flush=True)
        report["complete"] = True
    finally:
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
