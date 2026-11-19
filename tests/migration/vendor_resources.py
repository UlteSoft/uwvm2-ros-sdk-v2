"""@brief Verify one local original resource for each of four specialized migration examples."""
import argparse
import json
import os
from pathlib import Path
import sys

from platform_examples import ROOT, Source, install, sha, run, qualify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="JSON object mapping each platform to the original repository or package directory")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--vm", type=Path, required=True)
    parser.add_argument("--xmake", type=Path, required=True)
    parser.add_argument("--c-site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = Path("/sys/fs/cgroup") / next(r[3:].lstrip("/") for r in Path("/proc/self/cgroup").read_text().splitlines() if r.startswith("0::"))
    if ((current / "memory.max").read_text().strip(), (current / "memory.swap.max").read_text().strip()) != (str(64 << 30), "0"):
        parser.error("use a 64 GiB memory cgroup with swap disabled")
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    supplied = json.loads(args.sources.read_bytes())
    report = {"complete": False, "vm": sha(args.vm), "cgroup": str(current), "commit": args.commit, "cases": []}
    try:
        for platform in ("boston_dynamics", "fourier", "nvidia-groot", "kinova"):
            original = Path(supplied[platform]).resolve(strict=True)
            install_result = install(Source(args.commit, ROOT), platform, "c", args.output / "installs",
                                     ["--component", "migration"], site_profile=args.c_site)
            sdk = Path(install_result["directory"])
            project = sdk / "examples/platform" / platform / "migration/c"
            manifest = project / "vendor-package.xml"
            root = original
            if manifest.exists():
                root = args.output / (platform + "-package")
                script = sdk / "examples/shared/migration/c/stage_vendor.py"
                run(args.output / (platform + "-stage.log"), [sys.executable, "-I", "-B", script,
                    "--project", project, "--source-root", original, "--output", root], args.output, os.environ)
            entry = qualify(args, platform, "c", {platform: root})
            entry["origin"] = "SDK mapping of original non-ROS resource" if manifest.exists() else "original ROS package"
            report["cases"].append(entry)
            print(platform, entry["input"]["uri"], flush=True)
        report["complete"] = True
    finally:
        (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
