"""Install Fortran at an exact commit and build and run the packaged xmake project."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from separate_compilation import ROOT, candidate_arguments, cgroup_record, inspect, sha
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "toolchain", "sysroots", "plain-sysroots", "runtime", "xmake", "output"):
        parser.add_argument("--" + key, required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--flang", type=lambda p: Path(p).resolve())
    parser.add_argument("--commit", required=True)
    parser.add_argument("--address-width", choices=(32, 64), type=int, required=True)
    parser.add_argument("--platform", default="unitree")
    candidate_arguments(parser)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    package = Path(install(Source(args.commit, args.repository), args.platform, "fortran", out / "sdk", [])["directory"])
    if (package / "language/lua").exists() or (package / "language/cpp").exists():
        raise AssertionError("unrequested language package installed")
    env = dict(os.environ, XMAKE_GLOBALDIR=str(out / "xmake"), XMAKE_ROOT="y",
               UWVM_ROS_SDK_ROOT=str(package), WROS_TOOLCHAIN=str(args.toolchain),
               WROS_SYSROOTS=str(args.sysroots), WROS_SYSROOTS_NO_MTE=str(args.plain_sysroots),
               WROS_VM=str(args.runtime), WROS_PLATFORM=args.platform, WROS_RUN_QUERIES="")
    if args.flang:
        env["WROS_FLANG"] = str(args.flang)
    record = dict(complete=False, cgroup=cgroup_record(), commit=args.commit, platform=args.platform,
                  address_bits=args.address_width, candidate_mte=args.candidate_mte, cases=[], modules={})
    report = out / "results.json"

    def save():
        report.write_text(json.dumps(record, indent=2) + "\n")

    def run(name, project, argv, expected=None, **settings):
        proc = subprocess.run([args.xmake, *argv], capture_output=True, env={**env, **settings},
                              cwd=project, timeout=300)
        log = proc.stdout + proc.stderr
        (out / (name + ".log")).write_bytes(log)
        record["cases"].append(dict(name=name, exit=proc.returncode, expected=expected))
        save()
        if (proc.returncode == 0) != (expected is None) or (expected and expected.encode() not in log):
            raise RuntimeError(name + ": " + log[-1600:].decode(errors="replace"))

    for mode in ("on", "off"):
        project = out / mode
        shutil.copytree(package / "examples/fortran", project)
        script = project / "xmake.lua"
        setting = '"legacy"' if args.candidate_mte else "true"
        script.write_text(script.read_text().replace("mte = true", "mte = " + (setting if mode == "on" else "false")))
        run(mode + "-configure", project, ["f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm"+str(args.address_width)])
        run(mode + "-build", project, ["-j1", "robot"])
        modules = list((project / "build").rglob("robot.wasm"))
        if len(modules) != 1:
            raise AssertionError("expected one Wasm program")
        rows = inspect(modules[0].read_bytes())
        if [(row["module"], row["name"]) for row in rows] != [("uwvm_ros_v2", "abi")]:
            raise AssertionError(rows)
        record["modules"][mode] = dict(sha256=sha(modules[0]), imports=rows)
        run(mode + "-denied", project, ["run", "robot"], expected="ROS scene interface is hidden")
        run(mode + "-granted", project, ["run", "robot"], WROS_RUN_QUERIES="abi")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
