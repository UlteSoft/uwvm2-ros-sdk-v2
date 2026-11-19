"""Reproduce the build-host closure from the two upstream release archives."""
import argparse
import gzip
import hashlib
import io
import json
import lzma
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
TS_SHA = "10e108c9cf7d5f2879053dff18515fb405abf2ccef63eaaf017d9c571687a1d3"
NODE_SHA = "2e5d13569282d016861fae7c8f935e741693c269101a5bebcf761a5376d1f99f"
NODE_BINARY = "e6ec2c188d83d813f81f2de8aea084d74dce603ac1abedd0a30ad941b10087b2"


def extract(archive, member):
    entry = archive.getmember(member)
    if not entry.isfile():
        raise ValueError("expected a regular archive member: " + member)
    return archive.extractfile(entry).read()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pack(typescript, node, output):
    for path, expected in ((typescript, TS_SHA), (node, NODE_SHA)):
        with path.open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != expected:
                raise ValueError("upstream archive digest mismatch: " + path.name)
    output.mkdir(parents=True, exist_ok=True)
    with tarfile.open(typescript) as package:
        files = {"typescript.js": extract(package, "package/lib/typescript.js")}
        pending = ["es2022"]
        while pending:
            filename = "lib." + pending.pop() + ".d.ts"
            if filename in files:
                continue
            contents = extract(package, "package/lib/" + filename)
            files[filename] = contents
            pending.extend(re.findall(r'<reference lib="([a-z0-9.]+)"', contents.decode()))
        for name in ("LICENSE.txt", "ThirdPartyNoticeText.txt"):
            (output / name).write_bytes(extract(package, "package/" + name))
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
        for name, contents in sorted(files.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(contents)
            bundle.addfile(entry, io.BytesIO(contents))
    compiler = gzip.compress(raw.getvalue(), compresslevel=6, mtime=0)
    (output / "compiler.tar.gz").write_bytes(compiler)
    with tarfile.open(node) as package:
        binary = extract(package, "node-v22.22.3-linux-x64/bin/node")
        if sha(binary) != NODE_BINARY:
            raise ValueError("unexpected Node executable")
        (output / "LICENSE-node").write_bytes(extract(package, "node-v22.22.3-linux-x64/LICENSE"))
    host = lzma.compress(binary, preset=2)
    (output / "node-linux-x64.xz").write_bytes(host)
    release = {"typescript": "5.9.3", "typescript_url": "https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz",
               "typescript_upstream_sha256": TS_SHA, "node": "22.22.3",
               "node_url": "https://nodejs.org/dist/v22.22.3/node-v22.22.3-linux-x64.tar.xz",
               "node_upstream_sha256": NODE_SHA, "node_binary_sha256": NODE_BINARY,
               "node_bytes": len(binary), "node_xz_sha256": sha(host), "compiler_sha256": sha(compiler),
               "files": {name: sha(data) for name, data in sorted(files.items())}}
    (output / "release.json").write_text(json.dumps(release, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("typescript", type=Path)
    parser.add_argument("node", type=Path)
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    pack(args.typescript, args.node, args.output)
