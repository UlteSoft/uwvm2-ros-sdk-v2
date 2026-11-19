"""@file run_guest.py
@brief Execute a built guest in a user-selected u2ros VM under a local test policy."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "install"))
from guest_profile import Profile
from artifacts import read_bounded
from frontend import audit
import subprocess
import tempfile


def main():
    """@brief Execute the audited artifact in the requested VM with scoped test permissions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    parser.add_argument("arch", choices=("wasm32", "wasm64"))
    parser.add_argument("core", choices=("mvp", "3.0"))
    parser.add_argument("thread_mode", choices=("threads", "single"))
    parser.add_argument("--engine", choices=("int", "aot"))
    parser.add_argument("--exceptions", choices=("eh", "noeh"), default="noeh")
    parser.add_argument("--check-tags", action="store_true")
    parser.add_argument("--queries", help="exact read-only query list for this local test")
    parser.add_argument("--driver-denial", metavar="PLATFORM", help="verify both denied driver routes with a private test peer")
    args = parser.parse_args()
    if args.driver_denial and (not args.engine or args.driver_denial != Path(__file__).resolve().parents[4].name):
        parser.error("the test platform must match the installed SDK selection")
    vm = Path(os.environ.get("WROS_VM", ""))
    if not vm.is_absolute() or not vm.is_file() or not os.access(vm, os.X_OK):
        parser.error("set WROS_VM to the absolute path of the trusted uwvm2-ros executable")
    bits = int(args.arch[4:])
    profile = Profile(bits, "1.0" if args.core == "mvp" else "3.0",
                      args.thread_mode == "threads", exceptions=args.exceptions)
    argv = [str(vm), *profile.uwvm_feature_flags(), "--wasm-set-main-module-name", "main"]
    if args.engine:
        argv += ["--runtime-" + args.engine, "--runtime-compile-threads", "0",
                 "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit"]
    if args.check_tags:
        argv += ["--runtime-memtag-mode", "sync"]
    # Only an operator running a local test can opt into these specific queries.
    queries = (args.queries if args.queries is not None else os.getenv("WROS_RUN_QUERIES", "")).split(",")
    if args.driver_denial and "abi" in queries:
        parser.error("the driver fixture owns its ROS environment")
    if queries != [""]:
        valid = {"abi", "realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution"}
        if any(q not in valid for q in queries):
            parser.error("WROS_RUN_QUERIES accepts " + ", ".join(sorted(valid)))
        if "abi" in queries:
            argv += ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                     "--ros-scene-interface", "robot", "abi", "allow"]
        clocks = sorted(set(queries) - {"abi"})
        if clocks:
            argv += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main"]
            suffix = "_wasm64" if bits == 64 else ""
            interfaces = {"clock_res_get" if q.endswith("-resolution") else "clock_time_get" for q in clocks}
            for name in sorted(interfaces):
                argv += ["--wasip1-single-interface", "main", name + suffix, "allow"]
            for q in clocks:
                argv += ["--wasip1-single-grant", "main", q]
    try:
        content = read_bounded(args.module)
        audit(content, profile)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    # The file can be replaced after validation. Give the VM the exact audited bytes.
    with tempfile.TemporaryDirectory(prefix="wros-core-") as directory:
        snapshot = Path(directory) / "guest.wasm"
        snapshot.write_bytes(content)
        if args.driver_denial:
            from platform_driver_test import check
            return check(argv, snapshot, args.driver_denial)
        status = subprocess.run([*argv, "--run", str(snapshot)]).returncode
    return status if status >= 0 else 128 - status


if __name__ == "__main__":
    raise SystemExit(main())
