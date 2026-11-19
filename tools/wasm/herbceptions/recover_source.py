#!/usr/bin/env python3
"""Reconstruct and verify the unmodified Herbceptions LLVM source in a fresh directory."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ARCHIVE = "llvm-23.1.5.tar.xz"
ARCHIVE_SHA256 = "78661f16b2c412b6d05579d25ef1ab5fe5691208bcb1f4f5ab816fc1f7cdc661"
FORK_COMMIT = "218014296779772a4edbe63eff3fe6fe0ba92390"
FORK_TREE = "69a2c7cbcfb0371010a4b5a02d0f73e14eef23ed"
DELTA = "llvm-herbceptions-21801429"
MANIFEST_SHA256 = "106362deb17ba87acbf95be422c0b0e2de11ebeb920ffa9a79f1d687224a7dbc"


def digest(file):
    with file.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def recover(output: Path, sdk_root: Path | None = None) -> Path:
    """Materialize the full fork tree, without applying SDK patches or running guest tools.

    The trusted SDK commit carries the original release archive and a delta over
    the exact Git tree recovered from it. The checkout is published atomically
    only after the fork's Git tree, file modes, symlinks and license all match.
    """
    root = Path(sdk_root).resolve() if sdk_root is not None else Path(__file__).resolve().parents[3]
    vendor = root / "third-parties/sources"
    package = vendor / DELTA
    descriptor = package / "source.json"
    with descriptor.open("rb") as stream:
        data = stream.read(4097)
    if len(data) > 4096 or hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise ValueError("fork release descriptor hash mismatch")
    manifest = json.loads(data)
    base, patch = manifest["base"], manifest["patch"]
    if (manifest["format"] != "wros-llvm-source-delta" or manifest["commit"] != FORK_COMMIT
            or manifest["tree"] != FORK_TREE or base["archive"] != ARCHIVE
            or base["archive_sha256"] != ARCHIVE_SHA256 or base["root"] != "llvm-23.1.5"):
        raise ValueError("unexpected LLVM source release descriptor")
    if patch["format"] != "git-binary-diff" or patch["compression"] != "xz":
        raise ValueError("unrecognized fork delta format")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("choose a fresh destination: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        stage = Path(scratch)
        env = {"PATH": os.defpath, "LC_ALL": "C", "TMPDIR": scratch,
               "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}

        def cmd(*args, cwd=stage):
            return subprocess.run(args, cwd=cwd, env=env, check=True, text=True,
                                  stdout=subprocess.PIPE).stdout.strip()

        packed = stage / "delta.xz"
        with packed.open("xb") as dest:
            for index, item in enumerate(patch["parts"]):
                if item["name"] != f"part-{index:03d}":
                    raise ValueError("unexpected delta chunk name")
                part = package / item["name"]
                if part.stat().st_size != item["size"] or digest(part) != item["sha256"]:
                    raise ValueError("fork delta chunk hash mismatch")
                with part.open("rb") as stream:
                    shutil.copyfileobj(stream, dest, 1024 * 1024)
        if packed.stat().st_size != patch["compressed_size"] or digest(packed) != patch["compressed_sha256"]:
            raise ValueError("fork delta archive hash mismatch")

        archive = stage / ARCHIVE
        with archive.open("xb") as dest:
            for index, count in enumerate((33554432,) * 5 + (11443268,)):
                part = vendor / ARCHIVE / f"part-{index:03d}"
                if part.stat().st_size != count:
                    raise ValueError("vendored LLVM base archive chunk size mismatch")
                with part.open("rb") as stream:
                    shutil.copyfileobj(stream, dest, 1024 * 1024)
        if digest(archive) != ARCHIVE_SHA256:
            raise ValueError("vendored LLVM base archive hash mismatch")
        # Operate only on the pinned upstream archive using GNU tar's default
        # traversal protections; never restore ownership or special permissions.
        cmd("tar", "-xJf", archive, "--no-same-owner", "--no-same-permissions")
        archive.unlink()
        tree = stage / base["root"]
        if not tree.is_dir() or tree.is_symlink() or (tree / ".git").exists():
            raise ValueError("unexpected archived source directory")

        def git(*args):
            return cmd("git", "-c", "core.autocrlf=false", "-c", "core.hooksPath=/dev/null",
                       "-c", "gc.auto=0", *args, cwd=tree)

        git("init", "-q")
        git("add", "--force", "--all")
        if git("write-tree") != base["tree"]:
            raise ValueError("upstream archive produced an unexpected Git tree")
        patchfile = stage / "changes.patch"
        with lzma.open(packed, "rb") as stream, patchfile.open("xb") as dest:
            while block := stream.read(1024 * 1024):
                if dest.tell() + len(block) > patch["size"]:
                    raise ValueError("decoded delta exceeds the release size")
                dest.write(block)
        if patchfile.stat().st_size != patch["size"] or digest(patchfile) != patch["sha256"]:
            raise ValueError("invalid restored fork delta")
        git("apply", "--binary", "--index", "--whitespace=nowarn", str(patchfile))
        if git("write-tree") != FORK_TREE:
            raise ValueError("reconstructed fork tree differs from the recorded upstream commit")
        if manifest["license"]["path"] != "LICENSE.TXT" or digest(tree / "LICENSE.TXT") != manifest["license"]["sha256"]:
            raise ValueError("reconstructed upstream license hash mismatch")
        # Working-tree CRLF rules can transform bytes, including test fixtures.
        # Write only tracked blobs to a fresh tree with checkout conversions disabled.
        (tree / ".git/info/attributes").write_text("* -text -crlf !eol -ident -filter !working-tree-encoding\n")
        clean = stage / "verified-source"
        clean.mkdir()
        git("checkout-index", "--all", "--prefix=" + str(clean) + "/")
        clean.rename(output)
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--sdk-root", type=Path)
    a = p.parse_args()
    print(recover(a.output, a.sdk_root))
