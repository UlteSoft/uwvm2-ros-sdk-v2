"""Register the native Rust package descriptor produced by rebuild.py in a release checkout."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "install"))
from install import digest, native_packages, unpack_executable


def register(source):
    source = source.resolve(strict=True)
    descriptor = json.loads((source / "rust-packages.json").read_bytes())
    directory = ROOT / "bin/packages/linux-x86_64"
    catalog = directory / "manifest.json"
    directory = directory / "wrrs"
    directory.mkdir(exist_ok=True)
    scratch = ROOT / ".tmp/rust-register"
    scratch.mkdir(exist_ok=True, parents=True)
    with (scratch / "lock").open("a") as lock, tempfile.TemporaryDirectory(dir=scratch) as work:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = json.loads(catalog.read_bytes())
        packages, artifacts = descriptor["packages"], descriptor["artifacts"]
        if (set(packages) != set(artifacts) or artifacts.get("wrrs") != ["bin/wrrs", "bin/rustc"]
                or any(key != "wrrs" and not key.startswith("wrrs-") for key in packages)):
            raise ValueError("expected a complete native wrrs package descriptor")
        owner = manifest["selections"]["rust"]
        previous = set(owner["artifacts"])
        if (set(manifest["packages"]) - previous) & set(packages):
            raise ValueError("Rust package key collides with a different release")
        for key in previous:
            del manifest["packages"][key]
        manifest["packages"].update(packages)
        owner["artifacts"] = artifacts
        owner["system_libraries"] = descriptor["system_libraries"]
        selected = native_packages(manifest, artifacts, "wrrs")
        pending = []
        for rel, (metadata, _) in selected.items():
            dest = ROOT / rel
            expected_name = metadata["member"] + "-" + metadata["compressed_sha256"][:20] + ".tar.xz"
            if dest.parent != directory or dest.name != expected_name:
                raise ValueError("expected content-addressed package below the host catalog")
            archive = Path(work) / dest.name
            shutil.copyfile(source / dest.name, archive)
            unpack_executable(archive, metadata, Path(work) / metadata["member"])
            if dest.exists():
                if digest(dest) != metadata["compressed_sha256"]:
                    raise ValueError("previous file differs at immutable package path " + str(dest))
            else:
                pending.append((archive, dest))
        replacement = Path(work) / "manifest.json"
        replacement.write_text(json.dumps(manifest, indent=2) + "\n")
        for archive, dest in pending:
            os.replace(archive, dest)
        os.replace(replacement, catalog)
    print(catalog)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--from", dest="source", required=True, type=Path)
    try:
        register(cli.parse_args().source)
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(f"Rust release registration failed: {error}")
