#!/usr/bin/env python3
"""Install one platform and language from the official WROS SDK repository."""
import argparse
import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


REPO = "UlteSoft/uwvm2-ros-sdk-v2"
REPOSITORY = f"https://github.com/{REPO}.git"
ENTRY = "install/install.py"
COMMIT = re.compile(r"[0-9a-f]{40}")
MAX_ENTRY = 256 * 1024


def git_environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
               GIT_ALLOW_PROTOCOL="https", GIT_LFS_SKIP_SMUDGE="1", LC_ALL="C")
    return env


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        return None


def read_github(opener, request, read):
    for attempt in range(3):
        delay = 2 ** attempt
        try:
            with opener.open(request, timeout=60) as response:
                return read(response)
        except urllib.error.HTTPError as error:
            with error:
                if error.code in (403, 429):
                    after = error.headers.get("Retry-After", "")
                    reset = error.headers.get("X-RateLimit-Reset", "")
                    exhausted = error.headers.get("X-RateLimit-Remaining") == "0"
                    waits = []
                    if after.isdecimal():
                        waits.append(int(after))
                    if exhausted and reset.isdecimal():
                        waits.append(int(reset) - int(time.time()) + 1)
                    if waits:
                        delay = max(delay, *waits)
                    elif error.code == 429 or exhausted or b"rate limit" in error.read(1024).lower():
                        delay = 60 * 2 ** attempt
                    else:
                        raise
                    if delay > 60 or attempt == 2:
                        raise OSError(f"GitHub rate limit (HTTP {error.code}), retry in {delay} seconds") from None
                elif error.code not in (408, 500, 502, 503, 504) or attempt == 2:
                    raise
        except (OSError, http.client.HTTPException):
            if attempt == 2:
                raise
        time.sleep(delay)


def read_github_blob(opener, revision, name, oid, read):
    api = f"https://api.github.com/repos/{REPO}"

    def get(url):
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github.raw+json"})
        return read_github(opener, request, read)

    try:
        return get(f"{api}/git/blobs/{oid}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    return get(f"{api}/contents/{urllib.parse.quote(name)}?ref={revision}")


def bounded_response(response, limit):
    length = response.headers.get("Content-Length")
    if length is not None and not 0 <= int(length) <= limit:
        raise ValueError("oversized GitHub response")
    data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("oversized GitHub response")
    if length is not None and len(data) != int(length):
        raise OSError("incomplete GitHub response")
    return data


def raw_entry(revision, oid):
    opener = urllib.request.build_opener(NoRedirect())

    def verified(data):
        return (0 < len(data) <= MAX_ENTRY
                and hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == oid)

    url = f"https://raw.githubusercontent.com/{REPO}/{revision}/{ENTRY}"
    try:
        data = read_github(opener, url, lambda response: bounded_response(response, MAX_ENTRY))
        if verified(data):
            return data
    except (OSError, http.client.HTTPException, ValueError):
        pass

    data = read_github_blob(opener, revision, ENTRY, oid,
                            lambda response: bounded_response(response, 2 * MAX_ENTRY + 4096))
    if verified(data):
        return data
    # A proxy can return the default JSON representation despite the requested media type.
    try:
        record = json.loads(data)
    except (ValueError, RecursionError):
        raise ValueError("GitHub returned an invalid installer blob") from None
    if (not isinstance(record, dict) or record.get("sha") != oid or record.get("encoding") != "base64"
            or type(record.get("size")) is not int or not 0 < record["size"] <= MAX_ENTRY
            or not isinstance(record.get("content"), str)):
        raise ValueError("invalid installer blob metadata")
    data = base64.b64decode(b"".join(record["content"].encode("ascii").split()), validate=True)
    if len(data) != record["size"] or not verified(data):
        raise ValueError("installer Git blob verification failed")
    return data


def fetch_entry(directory, revision, env):
    def git(*args):
        return subprocess.check_output(["git", "-C", directory, "-c", "protocol.version=2",
                                        "-c", "http.followRedirects=false", *args], env=env)

    def retry_git(*args):
        for attempt in range(3):
            try:
                return git(*args)
            except subprocess.CalledProcessError:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    if revision is None:
        remote = retry_git("ls-remote", "--exit-code", REPOSITORY, "refs/heads/main").decode("ascii").split()
        if len(remote) != 2 or remote[1] != "refs/heads/main":
            raise ValueError("could not resolve the official main branch")
        revision = remote[0]
    if not COMMIT.fullmatch(revision):
        raise ValueError("--commit requires the complete lowercase 40-character commit ID")
    git("init", "--bare", "--quiet", "--template=")
    git("config", "gc.auto", "0")
    git("config", "fetch.fsckObjects", "true")
    git("config", "http.followRedirects", "false")
    # A cached upload-pack advertisement can predate the pinned release object.
    git("config", "http.extraHeader", "Cache-Control: no-cache")
    git("remote", "add", "origin", REPOSITORY)
    git("config", "remote.origin.promisor", "true")
    git("config", "remote.origin.partialclonefilter", "blob:none")
    fetch = ("fetch", "--quiet", "--no-tags", "--no-recurse-submodules", "--depth=1")
    try:
        retry_git(*fetch, "--filter=blob:none", "origin", revision)
        fetched = git("rev-parse", "--verify", "FETCH_HEAD^{commit}")
    except subprocess.CalledProcessError:
        # A stale upload-pack can refuse the commit-and-trees request. Request just
        # the pinned commit, then let Git fetch its trees by their verified IDs.
        git(*fetch, "--filter=tree:0", "origin", revision)
        git("config", "remote.origin.partialclonefilter", "blob:none")
        fetched = git("rev-parse", "--verify", "FETCH_HEAD^{commit}")
    if fetched.decode("ascii").strip() != revision:
        raise ValueError("GitHub returned a different commit")
    entry = git("ls-tree", "-z", revision, "--", ENTRY).rstrip(b"\0").split(b"\t")
    if len(entry) != 2 or entry[1] != ENTRY.encode():
        raise ValueError(f"{revision} has no {ENTRY}. Use the root installer shipped with that revision.")
    mode, kind, oid = entry[0].decode("ascii").split()
    if mode not in ("100644", "100755") or kind != "blob" or not COMMIT.fullmatch(oid):
        raise ValueError("unexpected installer tree entry")
    size = None
    try:
        size = int(git("cat-file", "-s", oid))
        if not 0 < size <= MAX_ENTRY:
            raise ValueError("invalid installer size")
        data = git("cat-file", "blob", oid)
    except subprocess.CalledProcessError:
        data = raw_entry(revision, oid)
        if size is None:
            size = len(data)
        stored = subprocess.check_output(["git", "-C", directory, "hash-object", "-w", "--stdin"], input=data, env=env)
        if stored.strip() != oid.encode():
            raise ValueError("could not store the verified installer Git blob")
    if len(data) != size or hashlib.sha1(f"blob {size}\0".encode() + data).hexdigest() != oid:
        raise ValueError("installer Git object verification failed")
    return revision, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("install", "plan", "list", "rebuild"), default="install",
                        help="install prebuilt packages (default), plan a selection, list it, or rebuild from source")
    parser.add_argument("--commit", help="pin a full Git commit (default: resolve main once)")
    parser.add_argument("--language", help="language ID from the selected revision (see list), for example c, cpp, rust, go, tinygo, py (python) or wat")
    parser.add_argument("--platform", default="generic", help="platform ID from the selected revision (see list)")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--mode", choices=("binary", "source", "bindings"),
                       help="install defaults to binary; plan --mode source previews a rebuild")
    modes.add_argument("--source", dest="mode", action="store_const", const="source", help="alias for --mode source")
    parser.add_argument("--no-mte", action="store_true", help="select compatibility bindings built by an external Rust compiler")
    parser.add_argument("--prefix", type=Path, default=Path.home() / ".local/share/wros-sdk")
    parser.add_argument("--bootstrap", type=Path, help="host LLVM installation for a C/C++ or TinyGo source build")
    parser.add_argument("--rust-bin", type=Path, help="use installed official Rust host tools for a Rust compiler build (1.97.1) or wrwat build (1.98.0)")
    parser.add_argument("--jobs", type=int, metavar="N", help="parallel jobs for source rebuilds")
    args = parser.parse_args()
    if args.action == "install" and args.mode == "source":
        parser.error("install only installs prebuilt inputs; use the rebuild action for a source build")
    if args.action == "rebuild" and args.mode not in (None, "source"):
        parser.error("rebuild requires source mode")
    if args.action != "list" and not args.language:
        parser.error("--language is required for install, plan and rebuild")
    if args.commit is not None and not COMMIT.fullmatch(args.commit):
        parser.error("--commit requires a complete lowercase 40-character commit ID")
    if args.jobs is not None and args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.jobs is not None and args.action == "list":
        parser.error("--jobs applies to rebuild or a selection")

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
        # Older second stages accepted --mode binary and still compiled host tools.
        # A stage that predates this protocol must reject the request before installation.
        if args.action in ("install", "plan") and args.mode != "source":
            command.append("--prebuilt-only")
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
    except (OSError, ValueError, http.client.HTTPException, subprocess.CalledProcessError) as error:
        sys.exit(f"Installation failed: {error}")
