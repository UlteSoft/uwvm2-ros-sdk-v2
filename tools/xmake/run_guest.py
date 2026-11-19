"""@file run_guest.py
@brief Execute a built guest in a user-selected u2ros VM under a local test policy."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "install"))
from guest_profile import Profile
from artifacts import read_bounded, sections
from frontend import audit
import subprocess
import tempfile



def require_test_entry(data):
    """@brief Require a module-defined entry before counting a VM run as a guest test.

    @details The import audit admits only function imports. Function indices start
    with these imports, followed by the functions declared by the guest. The VM
    validates section ordering, function signatures and bodies on instantiation.
    """
    imported = 0
    defined = 0
    entries = []
    for offset, _, _, body in sections(data):
        kind = data[offset]
        if kind == 2:
            imported = body.count()
        elif kind == 3:
            defined = body.count()
        elif kind == 7:
            for _ in range(body.count()):
                name, export_kind, index = body.name(), body.byte(), body.uint()
                if name == "_start":
                    if export_kind != 0:
                        raise ValueError("the test entry _start must export a function")
                    entries.append(index)
        elif kind == 8:
            entries.append(body.uint())
            body.end()
    if not entries or any(index < imported or index >= imported + defined for index in entries):
        raise ValueError("the test requires a module-defined _start or start function")



def resolve_test_queries(project, operator):
    """@brief Resolve the read-only grants for a local guest test.
    @param project Comma-separated queries declared by the project, or None.
    @param operator Optional local selection. An explicitly empty value denies all.
    @return The project grants remaining after the local selection is applied.
    """
    allowed = {"abi", "realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution"}

    def parse(value):
        queries = value.split(",") if value else []
        if not set(queries) <= allowed:
            raise ValueError("unknown test query; allowed values: " + ", ".join(sorted(allowed)))
        return queries

    if project is None:
        return parse(operator)
    requested = parse(project)
    if operator is None:
        return requested
    limits = set(parse(operator))
    return [q for q in requested if q in limits]


def main():
    """@brief Execute the audited artifact in the requested VM with scoped test permissions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    parser.add_argument("arch", choices=("wasm32", "wasm64"))
    parser.add_argument("core", choices=("mvp", "3.0"))
    parser.add_argument("thread_mode", choices=("threads", "single"))
    parser.add_argument("--engine", choices=("int", "aot"))
    parser.add_argument("--exceptions", choices=("eh", "noeh"), default="noeh")
    tags = parser.add_mutually_exclusive_group()
    tags.add_argument("--check-tags", action="store_true", help="check memory tags synchronously")
    tags.add_argument("--disable-tags", action="store_true", help="run the selected non-MTE profile")
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
                      args.thread_mode == "threads", mte=not args.disable_tags, exceptions=args.exceptions)
    argv = [str(vm), *profile.uwvm_feature_flags(), "--wasm-set-main-module-name", "main"]
    if args.engine:
        workers = os.getenv("WROS_TEST_AOT_WORKERS", "0") if args.engine == "aot" else "0"
        if not workers.isascii() or not workers.isdecimal():
            parser.error("WROS_TEST_AOT_WORKERS must be a nonnegative decimal count")
        argv += ["--runtime-" + args.engine, "--runtime-compile-threads", workers,
                 "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit"]
        if args.engine == "aot":
            argv += ["--runtime-llvm-jit-policy", "fast-compile"]
    if args.check_tags:
        argv += ["--runtime-memtag-mode", "sync"]
    elif args.disable_tags:
        argv += ["--runtime-disable-memtag"]
    # Only an operator running a local test can opt into these specific queries.
    try:
        queries = resolve_test_queries(args.queries, os.getenv("WROS_RUN_QUERIES"))
    except ValueError as error:
        parser.error(str(error))
    if args.driver_denial and "abi" in queries:
        parser.error("the driver fixture owns its ROS environment")
    if queries:
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
        if args.engine:
            require_test_entry(content)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    # The file can be replaced after validation. Give the VM the exact audited bytes.
    with tempfile.TemporaryDirectory(prefix="wros-core-") as directory:
        snapshot = Path(directory) / "guest.wasm"
        snapshot.write_bytes(content)
        if args.driver_denial:
            from platform_driver_test import check
        try:
            if args.driver_denial:
                return check(argv, snapshot, args.driver_denial)
            status = subprocess.run([*argv, "--run", str(snapshot)], timeout=600 if args.engine else None).returncode
        except subprocess.TimeoutExpired:
            print(f"WROS {args.engine} test: VM timed out after 600 seconds", file=sys.stderr)
            return 124
        if args.engine and status:
            outcome = f"exit {status}" if status > 0 else f"signal {-status}"
            print(f"WROS {args.engine} test: VM {outcome}", file=sys.stderr)
    return status if status >= 0 else 128 - status


if __name__ == "__main__":
    raise SystemExit(main())
