"""Install the official Roslyn, reference assemblies and Mono cross compiler for wrcs and wrvb."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

from host import LOCK, REF_PACK, sha


def materialize(prefix, cache=None):
    inputs = {name: digest for digest, name in
              (line.split("  ", 1) for line in LOCK.read_text().splitlines())}
    if prefix.exists():
        if not all(sha(prefix / name) == digest for name, digest in inputs.items()):
            raise ValueError("existing managed compiler differs from the SDK input lock")
        return
    prefix.parent.mkdir(parents=True, exist_ok=True)
    packages = json.loads(Path(__file__).with_name("packages.json").read_bytes())
    with tempfile.TemporaryDirectory(dir=prefix.parent) as temporary:
        work = Path(temporary)
        target = work / "inputs"
        expected = dict(inputs)

        def extract(relative, stream):
            if relative not in inputs:
                return
            digest = expected.pop(relative)
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as dst:
                shutil.copyfileobj(stream, dst)
            if sha(path) != digest:
                raise ValueError("incorrect managed compiler input: " + relative)
            path.chmod(0o755 if relative in ("dotnet/dotnet", "compiler/bin/mono-aot-cross") else 0o644)

        for package in packages:
            name = package["name"]
            archive = (cache or work) / name
            if cache is None:
                with urllib.request.urlopen(package["url"], timeout=90) as src, archive.open("xb") as dst:
                    size = 0
                    while block := src.read(1024 * 1024):
                        size += len(block)
                        if size > package["bytes"]:
                            raise ValueError("download exceeds the official package size: " + name)
                        dst.write(block)
            with archive.open("rb") as src:
                if (os.fstat(src.fileno()).st_size != package["bytes"] or
                        hashlib.file_digest(src, "sha512").hexdigest() != package["sha512"]):
                    raise ValueError("package differs from the official release: " + name)
                src.seek(0)
                if name.endswith(".tar.gz"):
                    with tarfile.open(fileobj=src, mode="r|gz") as tar:
                        for member in tar:
                            relative = "dotnet/" + Path(member.name).as_posix()
                            if member.isfile() and relative in inputs:
                                with tar.extractfile(member) as content:
                                    extract(relative, content)
                else:
                    with zipfile.ZipFile(src) as z:
                        for member in z.infolist():
                            if package["role"] == "runtime":
                                relative = f"dotnet/packs/Microsoft.NETCore.App.Runtime.Mono.wasi-wasm/{REF_PACK}/" + member.filename
                            else:
                                relative = {"tools/mono-aot-cross": "compiler/bin/mono-aot-cross",
                                            "tools/libc++.so.1": "compiler/lib/libc++.so.1",
                                            "tools/libc++abi.so.1": "compiler/lib/libc++abi.so.1"}.get(member.filename)
                            if relative in inputs:
                                with z.open(member) as content:
                                    extract(relative, content)
        if expected:
            raise ValueError("official packages lack a locked input: " + min(expected))
        target.rename(prefix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    parser.add_argument("--cache", type=Path, help="use the three official archives already in this directory")
    args = parser.parse_args()
    try:
        materialize(args.prefix.absolute(), args.cache)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, tarfile.TarError) as exc:
        parser.exit(1, str(exc) + "\n")
