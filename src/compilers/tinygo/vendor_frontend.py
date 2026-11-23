"""Export the editable native TinyGo build inputs from pinned LLVM and Go sources."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
LLVM_ROOTS = ("LICENSE.TXT", "clang", "cmake", "libunwind", "lld", "llvm", "third-party")
TEST_TREES = ("clang/test/", "clang/unittests/", "clang/bindings/python/tests/",
              "libunwind/test/", "lld/test/", "lld/unittests/", "llvm/test/",
              "llvm/unittests/", "llvm/utils/lit/tests/")


def output(*args, **kwargs):
    return subprocess.check_output(list(map(str, args)), **kwargs)


def check_source_file(path, data):
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"} or re.search(
        rb"-----BEGIN (?:[A-Z0-9]+ )*(?:PRIVATE KEY|CERTIFICATE)-----", data
    ):
        raise ValueError(f"unexpected key or PEM fixture in compiler sources: {path}")


def record(digest, path, mode, data):
    digest.update(path.encode() + b"\0" + mode.encode() + b"\0" + hashlib.sha256(data).digest())


def export_llvm(project, destination, pin):
    revision = output("git", "-C", project, "rev-parse", "HEAD", "HEAD^{tree}").decode().splitlines()
    if revision != [pin["commit"], pin["tree"]]:
        raise ValueError("Espressif source does not match the recorded Git commit and tree")
    listing = output("git", "-C", project, "ls-tree", "-rz", revision[0], "--", *LLVM_ROOTS)
    digest = hashlib.sha256()
    count = 0
    entries = []
    for line in listing.split(b"\0"):
        if line:
            header, name = line.decode().split("\t", 1)
            if not name.startswith(TEST_TREES):
                entries.append((name, *header.split()))
    for name, mode, kind, oid in sorted(entries):
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"unexpected compiler source entry: {name}")
        data = (project / name).read_bytes()
        if hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() != oid:
            raise ValueError(f"LLVM source differs from Git: {name}")
        path = destination / name
        check_source_file(path, data)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(int(mode[-3:], 8))
        record(digest, name, mode, data)
        count += 1
    return dict(commit=revision[0], tree=revision[1], roots=LLVM_ROOTS,
                omitted_test_trees=TEST_TREES, files=count, source_sha256=digest.hexdigest())


def export_modules(goroot, modcache, scratch, destination):
    version = (goroot / "VERSION").read_text().splitlines()[0]
    if version != "go1.24.2":
        raise ValueError("expected Go 1.24.2")
    source = scratch / "tinygo"
    shutil.copytree(ROOT / "upstream", source)
    env = dict(os.environ, GOROOT=str(goroot), GOMODCACHE=str(modcache), GOPROXY="off",
               GOSUMDB="off", GOTOOLCHAIN="local", GOWORK="off", GOENV="off", GOFLAGS="",
               GOOS="linux", GOARCH="amd64", GOCACHE=str(scratch / "go-cache"), GOTMPDIR=str(scratch),
               XDG_CACHE_HOME=str(scratch / "cache"), XDG_CONFIG_HOME=str(scratch / "config"), TMPDIR=str(scratch))
    go = goroot / "bin/go"
    output(go, "mod", "verify", cwd=source, env=env)
    output(go, "mod", "vendor", "-o", destination, cwd=source, env=env)
    sums = set((ROOT / "upstream/go.sum").read_text().splitlines())
    modules = []
    for line in (destination / "modules.txt").read_text().splitlines():
        if not line.startswith("# "):
            continue
        _, name, version_number = line.split()
        module = json.loads(output(go, "mod", "download", "-json", f"{name}@{version_number}", cwd=source, env=env))
        if (f"{name} {version_number} {module['Sum']}" not in sums or
                f"{name} {version_number}/go.mod {module['GoModSum']}" not in sums):
            raise ValueError(f"module or go.mod differs from TinyGo's upstream go.sum: {name}")
        modules.append(dict(path=name, version=version_number, sum=module["Sum"], go_mod_sum=module["GoModSum"]))
    digest = hashlib.sha256()
    count = 0
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            check_source_file(path, data)
            record(digest, path.relative_to(destination).as_posix(), "100755" if path.stat().st_mode & 0o111 else "100644", data)
            count += 1
    return dict(go=version, go_sum_sha256=hashlib.sha256((ROOT / "upstream/go.sum").read_bytes()).hexdigest(),
                files=count, source_sha256=digest.hexdigest(), modules=modules)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm-source", "goroot", "modcache", "work", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    destination = args.output.resolve()
    if destination.exists():
        parser.error("--output must be a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    pin = json.loads((ROOT / "upstream.json").read_text())["frontend_llvm"]
    with tempfile.TemporaryDirectory(dir=args.work.resolve()) as tmp, tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        tree = Path(staging) / "frontend"
        lock = dict(llvm=export_llvm(args.llvm_source.resolve(), tree / "llvm-project", pin),
                    go=export_modules(args.goroot.resolve(), args.modcache.resolve(), Path(tmp), tree / "vendor"))
        (tree / "sources.json").write_text(json.dumps(lock, indent=2) + "\n")
        tree.rename(destination)


if __name__ == "__main__":
    main()
