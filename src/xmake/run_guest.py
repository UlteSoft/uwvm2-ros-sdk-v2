"""Execute the exported guest entry under the selected uwvm2-ros engine."""
import argparse
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def read(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("truncated WebAssembly module")
    return data


def uint(stream, width=32):
    value = 0
    for offset in range(0, width, 7):
        byte = read(stream, 1)[0]
        value |= (byte & 127) << offset
        if byte < 128 and value < 1 << width:
            return value
    raise ValueError("invalid unsigned LEB128 integer")


def name(stream):
    return read(stream, uint(stream)).decode("utf-8")


def require_entry(blob):
    stream = BytesIO(blob)
    if read(stream, 8) != b"\0asm\x01\0\0\0":
        raise ValueError("expected a Core WebAssembly module")
    imported = defined = 0
    start = None
    imports = set()
    while tag := stream.read(1):
        size = uint(stream)
        if tag not in (b"\x02", b"\x03", b"\x07"):
            if stream.seek(size, 1) > len(blob):
                raise ValueError("section exceeds module")
            continue
        body = BytesIO(read(stream, size))
        count = uint(body)
        if tag == b"\x03":
            defined = count
            continue
        for _ in range(count):
            item = name(body)
            if tag == b"\x07":
                kind = read(body, 1)
                index = uint(body)
                if item == "_start":
                    if kind != b"\0" or start is not None:
                        raise ValueError("expected one function export named _start")
                    start = index
            else:
                field = name(body)
                kind = read(body, 1)
                if kind == b"\0":
                    uint(body)
                    imports.add((item, field))
                    imported += 1
                elif kind == b"\x02":
                    flags = uint(body)
                    width = 64 if flags & 4 else 32
                    uint(body, width)
                    if flags & 1:
                        uint(body, width)
                    if flags & 8:
                        uint(body)
                else:
                    raise ValueError("local runner supports function imports and explicitly declared guest memory")
    if start is None or not imported <= start < imported + defined:
        raise ValueError("execution requires a module-defined _start function")
    return imports


# A local standard Go command owns its argv, empty environment, startup clocks
# and normal process exit. With no preopen, fd_prestat_get(3) must reach the
# real WASI provider to return EBADF during the syscall package's startup scan.
GO_RUNTIME = {
    "args_sizes_get": ("args",), "args_get": ("args",),
    "environ_sizes_get": ("environ",), "environ_get": ("environ",),
    "clock_time_get": ("monotonic-clock", "realtime-clock"),
    "random_get": ("random",), "proc_exit": ("proc-exit",),
    "fd_prestat_get": (), "fd_write": ("stderr.write",),
    "poll_oneoff": ("monotonic-timer",),
}


PYTHON_RUNTIME = {
    "args_sizes_get": ("args",), "args_get": ("args",),
    "clock_time_get": ("monotonic-clock", "realtime-clock"),
    "clock_res_get": ("monotonic-resolution", "realtime-resolution"),
    "fd_fdstat_get": ("stdio.metadata",), "fd_filestat_get": ("stdio.metadata",),
    "fd_write": ("stdout.write", "stderr.write"), "proc_exit": ("proc-exit",),
    # Querying a nonexistent preopen must reach Preview1 and return EBADF.
    "fd_prestat_get": (), "fd_close": (),
}

# File descriptors inherit only the operations used to open and inspect paths,
# enumerate directories, and read and seek source files under the preopen.
PYTHON_FILE_INTERFACES = {"fd_prestat_dir_name", "path_open", "path_filestat_get", "fd_readdir",
                          "fd_read", "fd_seek", "fd_tell"}
PYTHON_PREOPEN_RIGHTS = (1 << 13) | (1 << 18)  # PATH_OPEN, PATH_FILESTAT_GET
PYTHON_CHILD_RIGHTS = (PYTHON_PREOPEN_RIGHTS | (1 << 14) | (1 << 21)  # FD_READDIR, FD_FILESTAT_GET
                       | (1 << 1) | (1 << 2) | (1 << 5))  # FD_READ, FD_SEEK, FD_TELL


def runtime_permissions(imports, allowed):
    flags = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
             "--wasip1-single-noinherit-system-environment", "main"]
    grants = set()
    for module, field in sorted(imports):
        if module != "wasi_snapshot_preview1":
            continue
        permissions = allowed.get(field.removesuffix("_wasm64"))
        flags.extend(["--wasip1-single-interface", "main", field, "allow" if permissions is not None else "deny"])
        if permissions:
            grants.update(permissions)
    for permission in sorted(grants):
        flags.extend(["--wasip1-single-grant", "main", permission])
    return flags


def python_file_permissions(imports, directory, script):
    directory = directory.resolve(strict=True)
    script = script.resolve(strict=True)
    if not directory.is_dir() or not script.is_file() or script.suffix != ".py" or not script.is_relative_to(directory):
        raise ValueError("the Python script must be a .py file within the explicitly selected read-only directory")
    required = {("wasi_snapshot_preview1", name) for name in PYTHON_FILE_INTERFACES}
    if not required <= imports:
        raise ValueError("this module lacks the shared CPython file imports; use the relinked shared interpreter")
    allowed = dict(PYTHON_RUNTIME, **dict.fromkeys(PYTHON_FILE_INTERFACES, ()))
    guest = "/guest/" + script.relative_to(directory).as_posix()
    return [*runtime_permissions(imports, allowed),
            "--wasip1-single-mount-dir", "main", "/guest", str(directory),
            "--wasip1-single-mount-dir-rights", "main", "/guest", str(PYTHON_PREOPEN_RIGHTS), str(PYTHON_CHILD_RIGHTS),
            "--wasip1-single-force-args", "main", "2", "cpython", guest]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("module", type=Path)
    p.add_argument("--workdir", type=Path, help="directory for the temporary execution snapshot")
    p.add_argument("--engine", choices=("int", "aot"), required=True)
    p.add_argument("--core", choices=("3.0", "mvp"), required=True)
    p.add_argument("--query", choices=("abi", "realtime-clock", "go-runtime", "python-runtime", "python-stdin"), action="append", default=[])
    p.add_argument("--python-read-only", type=Path, nargs=2, metavar=("DIRECTORY", "SCRIPT"),
                   help="mount one host directory at /guest and run its Python script by guest pathname")
    for key in ("eh", "mte", "memory64", "threads"):
        p.add_argument("--" + key, action=argparse.BooleanOptionalAction, required=True)
    args = p.parse_args()
    if args.python_read_only and (args.query or not args.mte or not args.eh or args.threads or args.core != "3.0"):
        p.error("--python-read-only requires the shared CPython Core 3.0, EH, MTE, no-threads profile and no queries")
    override = os.environ.get("WROS_VM")
    bundled = Path(__file__).resolve().parents[2] / "bin" / "uwvm2-ros"
    vm = Path(override) if override else bundled
    if not vm.is_absolute() or not vm.is_file() or not os.access(vm, os.X_OK):
        if override:
            p.error("WROS_VM must name an absolute executable file")
        p.error(f"missing SDK runtime {vm}; install the host tools or set WROS_VM to an absolute executable")
    with args.module.open("rb") as stream:
        limit = 128 * 1024 * 1024
        blob = stream.read(limit + 1)
    if len(blob) > limit:
        p.error("guest exceeds the 128 MiB local test limit")
    imports = require_entry(blob)
    # The VM accepts independent feature overrides after the baseline.
    command = [str(vm), "--wasm-feature-wasm3" if args.core == "3.0" else "--wasm-feature-wasmmvp"]
    for feature, enabled in (("memory64", args.memory64), ("table64", args.memory64),
                             ("exceptions", args.eh), ("threads", args.threads)):
        command.append("--wasm-feature-" + ("enable-" if enabled else "disable-") + feature)
    command += ["--runtime-" + args.engine, "--runtime-compile-threads", "0", "--debug-fault-action", "exit"]
    if args.engine == "aot":
        command += ["--runtime-llvm-jit-cache-path", "disable", "--runtime-llvm-jit-policy", "fast-compile"]
    command += ["--runtime-memtag-mode", "sync"] if args.mte else ["--runtime-disable-memtag"]
    command += ["--wasm-set-main-module-name", "main"]
    if "go-runtime" in args.query:
        command += runtime_permissions(imports, GO_RUNTIME)
    elif args.python_read_only:
        command += python_file_permissions(imports, *args.python_read_only)
    elif "python-runtime" in args.query or "python-stdin" in args.query:
        allowed = dict(PYTHON_RUNTIME)
        if "python-stdin" in args.query:
            allowed["fd_read"] = ("stdin.read",)
        command += runtime_permissions(imports, allowed)
        command += ["--wasip1-single-force-args", "main", "1", "cpython"]
    elif any(module == "wasi_snapshot_preview1" for module, _ in imports):
        allowed = {"clock_time_get": ("realtime-clock",)} if "realtime-clock" in args.query else {}
        command += runtime_permissions(imports, allowed)
    if "abi" in args.query:
        command += ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                    "--ros-scene-interface", "robot", "abi", "allow"]
        for module, field in sorted(imports):
            if module == "uwvm_ros_v2" and field != "abi":
                command += ["--ros-scene-interface", "robot", field, "deny"]
    with tempfile.TemporaryDirectory(dir=args.workdir or args.module.resolve().parent, prefix="run-") as directory:
        snapshot = Path(directory) / "guest.wasm"
        snapshot.write_bytes(blob)
        status = subprocess.run([*command, "--run", snapshot], timeout=600, cwd=directory).returncode
    return status if status >= 0 else 128 - status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        sys.exit(f"Guest execution failed: {error}")
