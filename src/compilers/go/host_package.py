"""Pack and materialize the Linux x86-64 Go and TinyGo WASI frontend inputs."""
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from official_dist import fetch_archive

UPSTREAM = {
    "go": ("go1.24.2.linux-amd64.tar.gz", "68097bd680839cbc9d464a0edce4f7c333975e27a90246890e9f1078c7e702ad"),
    "tinygo": ("tinygo0.38.0.linux-amd64.tar.gz", "edc3476ec69e309f0fd4afc1ec79c34e00a14bc3848a7133ac53f814e72faebd"),
}


def sha(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
        return digest.hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or not path.parts or ".." in path.parts or "\\" in name:
        raise ValueError(f"unexpected archive member {name!r}")
    return name


def selected(role, name):
    if role == "go":
        return name.startswith(("bin/", "src/", "lib/", "pkg/")) or name in ("go.env", "VERSION", "LICENSE", "PATENTS")
    return (name in ("bin/tinygo", "targets/wasip1.json", "LICENSE", "LICENSE-LLVM", "LICENSE.txt")
            or name.startswith(("lib/clang/", "lib/compiler-rt-builtins/", "lib/wasi-libc/", "src/device/arm/"))
            or (name.startswith("src/") and not name.startswith(("src/examples/", "src/machine/", "src/device/"))))


def unpack(role, dest, scratch, *, cache, without_tinygo_binary=False):
    """Install the selected members directly from the publisher's verified gzip archive."""
    from test_fixtures import sanitize

    filename, checksum = UPSTREAM[role]
    metadata = json.loads((Path(__file__).resolve().parent.parent / role / "upstream.json").read_bytes())
    if metadata["bootstrap"].rsplit("/", 1)[-1] != filename:
        raise ValueError("Go bootstrap URL differs from the pinned input")
    archive = fetch_archive(metadata["bootstrap"], checksum, cache)
    omissions = json.loads(Path(__file__).with_name("test-fixtures.json").read_bytes()) if role == "go" else {}
    with tempfile.TemporaryDirectory(dir=scratch, prefix="host-unpack-") as tmp:
        root = Path(tmp) / "root"
        with tarfile.open(archive, "r|gz") as source:
            for item in source:
                if item.isdir():
                    continue
                top, sep, name = safe_name(item.name).partition("/")
                if not sep or top != role:
                    raise ValueError("unexpected Go distribution member: " + item.name)
                if not selected(role, name) or (without_tinygo_binary and role == "tinygo" and name == "bin/tinygo"):
                    continue
                if not item.isfile():
                    raise ValueError("unexpected host file type: " + name)
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(item) as stream:
                    if name in omissions:
                        original = stream.read()
                        rule = omissions[name]
                        if hashlib.sha256(original).hexdigest() != rule["upstream_sha256"]:
                            raise ValueError("upstream fixture changed: " + name)
                        if rule["action"] == "omit":
                            continue
                        with path.open("xb") as output:
                            output.write(sanitize(original))
                    else:
                        with path.open("xb") as output:
                            shutil.copyfileobj(stream, output, 1 << 20)
                path.chmod(0o755 if item.mode & 0o111 else 0o644)
        dest.parent.mkdir(parents=True, exist_ok=True)
        root.rename(dest)
