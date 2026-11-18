"""Execute a built guest in a user-selected u2ros VM under a local test policy."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "install"))
from guest_profile import Profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    parser.add_argument("arch", choices=("wasm32", "wasm64"))
    parser.add_argument("core", choices=("mvp", "3.0"))
    parser.add_argument("thread_mode", choices=("threads", "single"))
    args = parser.parse_args()
    vm = Path(os.environ.get("WROS_VM", ""))
    if not vm.is_absolute() or not vm.is_file() or not os.access(vm, os.X_OK):
        parser.error("set WROS_VM to the absolute path of the trusted uwvm2-ros executable")
    bits = int(args.arch[4:])
    profile = Profile(bits, "1.0" if args.core == "mvp" else "3.0",
                      args.thread_mode == "threads", exceptions="noeh")
    argv = [str(vm), *profile.uwvm_feature_flags(), "--wasm-set-main-module-name", "main"]
    # Only an operator running a local test can opt into these specific queries.
    queries = os.getenv("WROS_RUN_QUERIES", "").split(",")
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
    os.execv(vm, [*argv, "--run", str(args.module.resolve(strict=True))])


if __name__ == "__main__":
    main()
