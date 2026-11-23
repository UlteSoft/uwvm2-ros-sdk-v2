#!/usr/bin/env python3
"""Run one SDK qualification phase in a nested 64 GiB cgroup and a clean mount namespace."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import uuid

LIMIT = "68719476736"
SLICE = "wrosvendor.slice"
ROOT = Path(__file__).resolve().parents[2]


def cgroup_info():
    """Check the parent and leaf OOM domains before launching the test command."""
    path = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines()
                if line.startswith("0::"))
    group = Path("/sys/fs/cgroup") / path.lstrip("/")
    if group.parent.name != SLICE:
        raise RuntimeError(f"expected a subgroup directly below {SLICE}, got {path}")

    def read_policy(directory, oom_group):
        expected = {"memory.max": LIMIT, "memory.swap.max": "0", "memory.oom.group": oom_group}
        observed = {name: (directory / name).read_text().strip() for name in expected}
        if observed != expected:
            raise RuntimeError(f"{directory} has cgroup policy {observed}, expected {expected}")
        return observed

    parent = read_policy(group.parent, "0")
    child = read_policy(group, "1")
    return {"cgroup": path, "parent_and_child_memory_max": int(parent["memory.max"]),
            "parent_and_child_swap_max": int(parent["memory.swap.max"]),
            "parent_memory_oom_group": int(parent["memory.oom.group"]),
            "child_memory_oom_group": int(child["memory.oom.group"])}


def sandbox(args, work):
    cgroup = cgroup_info()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    empty = work.parent / (".empty-" + uuid.uuid4().hex)
    empty.mkdir(mode=0o700)
    try:
        command = ["/usr/bin/bwrap", "--die-with-parent", "--new-session",
                   "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--clearenv",
                   "--proc", "/proc", "--dev", "/dev", "--ro-bind", str(empty), "/tmp",
                   "--ro-bind", str(empty), "/dev/shm", "--ro-bind", "/usr", "/usr"]
        if args.network == "offline":
            command.append("--unshare-net")
        for name in ("bin", "sbin", "lib", "lib64"):
            path = Path("/") / name
            if path.is_symlink():
                command.extend(["--symlink", os.readlink(path), str(path)])
            elif path.exists():
                command.extend(["--ro-bind", str(path), str(path)])
        for path in ("/etc/passwd", "/etc/group", "/etc/os-release", "/etc/alternatives",
                     "/etc/ld.so.cache", "/etc/ssl/certs", "/etc/hosts", "/etc/resolv.conf",
                     "/etc/nsswitch.conf", "/etc/gai.conf", "/etc/mime.types"):
            if Path(path).exists():
                command.extend(["--ro-bind", path, path])
        for name in ("home", "cache", "config", "data", "state", ".tmp"):
            (work / name).mkdir(mode=0o700, exist_ok=True)
        command.extend(["--bind", str(work), "/work", "--chdir", "/work"])
        environment = {
            "HOME": "/work/home", "TMPDIR": "/work/.tmp", "TMP": "/work/.tmp",
            "TEMP": "/work/.tmp", "XDG_CACHE_HOME": "/work/cache",
            "XDG_CONFIG_HOME": "/work/config", "XDG_DATA_HOME": "/work/data",
            "XDG_STATE_HOME": "/work/state", "XMAKE_TMPDIR": "/work/.tmp",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": "/opt/tools/bin:/usr/bin:/bin", "LC_ALL": "C", "XMAKE_STATS": "false",
            "XMAKE_GLOBALDIR": "/work/config/xmake",
        }
        for source, dest in ((args.vm, "/opt/tools/bin/uwvm2-ros"),
                             (args.xmake, "/opt/tools/bin/xmake"),
                             (args.xmake_data, "/opt/tools/share/xmake"),
                             (args.rust, "/opt/rust")):
            if source:
                command.extend(["--ro-bind", str(source.resolve(strict=True)), dest])
        if args.vm:
            environment["WROS_VM"] = "/opt/tools/bin/uwvm2-ros"
        if args.xmake_data:
            environment["XMAKE_PROGRAM_DIR"] = "/opt/tools/share/xmake"
        if args.rust:
            environment["PATH"] = "/opt/rust/bin:" + environment["PATH"]
        for key, value in environment.items():
            command.extend(["--setenv", key, value])
        print(json.dumps({**cgroup, "network": args.network,
                          "host_netns": os.readlink("/proc/self/ns/net"),
                          "host_mntns": os.readlink("/proc/self/ns/mnt")}), flush=True)
        # Bubblewrap constructs a fresh root. The work directory is its only writable disk mount.
        return subprocess.run([*command, "--remount-ro", "/", "--", *args.command]).returncode
    finally:
        empty.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inside-scope", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--network", choices=("online", "offline"), required=True)
    p.add_argument("--work", type=Path, required=True,
                   help="isolated phase directory beneath the SDK checkout's .tmp")
    p.add_argument("--vm", type=Path, help="VM under test")
    p.add_argument("--xmake", type=Path)
    p.add_argument("--xmake-data", type=Path)
    p.add_argument("--rust", type=Path, help="optional host Rust bootstrap distribution")
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.command[:1] == ["--"]:
        args.command.pop(0)
    if not args.command or bool(args.xmake) != bool(args.xmake_data):
        p.error("supply a command and both Xmake paths if Xmake is needed")
    work = args.work.resolve(strict=True)
    if not work.is_relative_to(ROOT / ".tmp") or work == ROOT / ".tmp":
        p.error("--work must be a directory inside the checkout's .tmp")
    if args.inside_scope:
        return sandbox(args, work)
    # The caller and the Codex process stay outside the job's OOM domain.
    return subprocess.run(["systemd-run", "--user", "--scope", "--collect",
                           "--slice=" + SLICE, "-p", "MemoryMax=" + LIMIT,
                           "-p", "MemorySwapMax=0", "-p", "OOMPolicy=kill",
                           sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                           "--inside-scope", *sys.argv[1:]]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
