#!/usr/bin/env python3
"""Link a self-contained Python project or execute a script with the installed shared CPython guest."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve()
SDK = HERE.parents[1] if HERE.parent.name == "bin" else HERE.parents[3]
sys.path.insert(0, str(SDK / "src/runtimes/cpython"))
from link import SHARED, link


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path, help="entry and explicitly included .py files")
    parser.add_argument("--entry", type=Path, help="main file when packaging a multi-file project")
    parser.add_argument("--project-root", type=Path, help="root for package names and source filenames")
    parser.add_argument("--platform", help="installed ROS platform")
    parser.add_argument("--ros-operation", action="append", default=[], metavar="IMPORT")
    parser.add_argument("--run", choices=("int", "aot"), help="execute one .py with the shared interpreter (stdin by default)")
    parser.add_argument("--read-only-dir", type=Path, metavar="DIRECTORY",
                        help="with --run, mount this directory at /guest and run its script by guest pathname")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-g", action="store_true", help="retain available guest DWARF on the linked application")
    parser.add_argument("--target", choices=("wasm32",), default="wasm32")
    parser.add_argument("--core", choices=("3.0",), default="3.0")
    for name, default in (("eh", True), ("mte", True), ("threads", False), ("memory64", True)):
        parser.add_argument("--" + name, action=argparse.BooleanOptionalAction, default=default)
    opts = parser.parse_args()
    if not opts.eh or not opts.mte or opts.threads:
        parser.error("published CPython requires wasm32 Core 3.0, EH, WasmMTE and one unshared memory")
    if opts.read_only_dir is not None and not opts.run:
        parser.error("--read-only-dir requires --run")
    selection = json.loads((SDK / "selection.json").read_bytes())
    platform = selection["platform"]
    if selection["language"] != "py" or platform not in ("generic", "unitree") or opts.platform not in (None, platform):
        parser.error("language and platform must match the installed Python selection")
    paths = [path.resolve(strict=True) for path in opts.sources]
    if any(path.suffix != ".py" or not path.is_file() for path in paths):
        parser.error("inputs must be regular .py files")
    if opts.run:
        if len(paths) != 1 or opts.output or opts.entry or opts.project_root or opts.ros_operation or opts.g:
            parser.error("--run takes one .py; use -o to package project modules or selected ROS imports")
        runner = SDK / "tools/xmake/run_guest.py"
        command = [sys.executable, "-I", "-B", runner, SDK / SHARED, "--engine", opts.run,
                   "--core", "3.0", "--eh", "--mte", "--no-threads",
                   "--memory64" if opts.memory64 else "--no-memory64"]
        if opts.read_only_dir is not None:
            return subprocess.run([*command, "--workdir", tempfile.gettempdir(),
                                   "--python-read-only", opts.read_only_dir, paths[0]], stdin=subprocess.DEVNULL).returncode
        with paths[0].open("rb") as source:
            return subprocess.run([*command, "--workdir", Path.cwd(), "--query", "python-stdin"],
                                  stdin=source).returncode
    if opts.output is None or (len(paths) > 1 and not opts.entry):
        parser.error("packaging requires -o PATH.wasm and --entry FILE for multiple sources")
    entry = opts.entry.resolve(strict=True) if opts.entry else paths[0]
    project = opts.project_root.resolve(strict=True) if opts.project_root else Path(os.path.commonpath([p.parent for p in paths]))
    link(SDK, opts.output, platform, project=project, entry=entry, sources=paths, names=opts.ros_operation, debug=opts.g)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        sys.exit("wrpy.py: " + str(error))
