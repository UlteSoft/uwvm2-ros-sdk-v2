"""Replay the SDK's QuickJS adaptations over its original official source release."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile


OFFICIAL_ARCHIVE_SHA256 = "b376e839b322978313d929fd20663b11ba58b75df5a46c126dd19ea2fa70ad2a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_manifest(directory):
    return json.loads((directory / "official-source.json").read_bytes())


def verify(directory, manifest):
    archive = directory / "quickjs-2026-06-04.tar.xz"
    if sha(archive.read_bytes()) != OFFICIAL_ARCHIVE_SHA256 or manifest["archive_sha256"] != OFFICIAL_ARCHIVE_SHA256:
        raise ValueError("official QuickJS distribution hash mismatch")
    packed = (directory / "official-source.patch.xz").read_bytes()
    if sha(packed) != manifest["patch_sha256"]:
        raise ValueError("QuickJS adaptation patch hash mismatch")
    files = manifest["files"]
    if set(files) != {p.name for p in directory.iterdir() if p.suffix in (".c", ".h")} | {"LICENSE"}:
        raise ValueError("QuickJS source inventory differs")
    with tempfile.TemporaryDirectory() as stage:
        out = Path(stage)
        with tarfile.open(archive, "r:xz") as dist:
            for name, row in files.items():
                if Path(name).name != name:
                    raise ValueError("invalid source basename")
                member = dist.getmember("quickjs-2026-06-04/" + name)
                if not member.isfile():
                    raise ValueError("expected regular source file")
                data = dist.extractfile(member).read()
                if sha(data) != row["source_sha256"]:
                    raise ValueError("source differs from the official archive: " + name)
                (out / name).write_bytes(data)
        patch = lzma.decompress(packed)
        if len(patch) != manifest["patch_bytes"]:
            raise ValueError("QuickJS adaptation patch size mismatch")
        env = {"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "init", "-q"], cwd=out, env=env, check=True)
        subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], input=patch, cwd=out, env=env, check=True)
        for name, row in files.items():
            if sha((out / name).read_bytes()) != row["sdk_sha256"] or sha((directory / name).read_bytes()) != row["sdk_sha256"]:
                raise ValueError("SDK source differs from the official release plus its recorded changes: " + name)
    return {"release": "2026-06-04", "archive_sha256": OFFICIAL_ARCHIVE_SHA256, "verified_files": len(files)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    directory = parser.parse_args().directory
    print(json.dumps(verify(directory, read_manifest(directory)), sort_keys=True))
