#!/usr/bin/env python3
"""Install one platform and language from the official WROS SDK repository."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPOSITORY = "https://github.com/UlteSoft/uwvm2-ros-sdk-v2.git"
ENTRY = "install/install.py"
COMMIT = re.compile(r"[0-9a-f]{40}")


def git_environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
               GIT_ALLOW_PROTOCOL="https", GIT_LFS_SKIP_SMUDGE="1", LC_ALL="C")
    return env


def fetch_entry(directory, revision, env):
    def git(*args):
        return subprocess.check_output(["git", "-C", directory, "-c", "protocol.version=2",
                                        "-c", "http.followRedirects=false", *args], env=env)

    if revision is None:
        remote = git("ls-remote", "--exit-code", REPOSITORY, "refs/heads/main").decode("ascii").split()
        if len(remote) != 2 or remote[1] != "refs/heads/main":
            raise ValueError("could not resolve the official main branch")
        revision = remote[0]
    if not COMMIT.fullmatch(revision):
        raise ValueError("--commit requires the complete lowercase 40-character commit ID")
    git("init", "--bare", "--quiet", "--template=")
    git("config", "gc.auto", "0")
    git("config", "fetch.fsckObjects", "true")
    git("config", "http.followRedirects", "false")
    git("remote", "add", "origin", REPOSITORY)
    git("config", "remote.origin.promisor", "true")
    git("config", "remote.origin.partialclonefilter", "blob:none")
    git("fetch", "--quiet", "--no-tags", "--no-recurse-submodules", "--depth=1",
        "--filter=blob:none", "origin", revision)
    if git("rev-parse", "FETCH_HEAD^{commit}").decode("ascii").strip() != revision:
        raise ValueError("GitHub returned a different commit")
    entry = git("ls-tree", "-z", revision, "--", ENTRY).rstrip(b"\0").split(b"\t")
    if len(entry) != 2 or entry[1] != ENTRY.encode():
        raise ValueError(f"{revision} has no {ENTRY}. Use the root installer shipped with that revision.")
    mode, kind, oid = entry[0].decode("ascii").split()
    if mode not in ("100644", "100755") or kind != "blob" or not COMMIT.fullmatch(oid):
        raise ValueError("unexpected installer tree entry")
    size = int(git("cat-file", "-s", oid))
    if not 0 < size <= 256 * 1024:
        raise ValueError("invalid installer size")
    data = git("cat-file", "blob", oid)
    if len(data) != size or hashlib.sha1(f"blob {size}\0".encode() + data).hexdigest() != oid:
        raise ValueError("installer Git object verification failed")
    return revision, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("install", "plan", "list"), default="install")
    parser.add_argument("--commit", help="pin a full Git commit (default: resolve main once)")
    parser.add_argument("--language", help="c, cpp, wat, or experimental rust")
    parser.add_argument("--platform", default="generic", help="platform ID from the selected revision (see list)")
    parser.add_argument("--mode", choices=("binary", "source", "bindings"))
    parser.add_argument("--no-mte", action="store_true", help="select the experimental upstream Rust bindings")
    parser.add_argument("--prefix", type=Path, default=Path.home() / ".local/share/wros-sdk")
    parser.add_argument("--bootstrap", type=Path, help="host LLVM installation for a C/C++ source build")
    parser.add_argument("--rust-bin", type=Path, help="directory containing the Rust source-build toolchain")
    parser.add_argument("--jobs", type=int, metavar="N", help="parallel jobs for a C/C++ source build")
    args = parser.parse_args()
    if args.action != "list" and not args.language:
        parser.error("--language is required for install and plan")
    if args.commit is not None and not COMMIT.fullmatch(args.commit):
        parser.error("--commit requires a complete lowercase 40-character commit ID")
    if args.jobs is not None and args.jobs < 1:
        parser.error("--jobs must be positive")

    prefix = args.prefix.expanduser().resolve()
    scratch = prefix / ".work"
    scratch.mkdir(parents=True, exist_ok=True)
    env = git_environment()
    with tempfile.TemporaryDirectory(prefix="fetch-", dir=scratch) as directory:
        workspace = Path(directory)
        repository = workspace / "objects.git"
        repository.mkdir()
        commit, entry = fetch_entry(repository, args.commit, env)
        bootstrap = workspace / "install.py"
        bootstrap.write_bytes(entry)
        command = [sys.executable, "-I", "-B", str(bootstrap), str(repository), commit, str(prefix),
                   args.action, "--platform", args.platform]
        for key in ("language", "mode", "bootstrap", "rust_bin", "jobs"):
            value = getattr(args, key)
            if value is not None:
                if isinstance(value, Path):
                    value = value.expanduser().resolve()
                command.extend(("--" + key.replace("_", "-"), str(value)))
        if args.no_mte:
            command.append("--no-mte")
        env["TMPDIR"] = str(workspace)
        return subprocess.run(command, env=env).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"Installation failed: {error}")
