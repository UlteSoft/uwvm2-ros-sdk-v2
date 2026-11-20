"""@file rebuild.py
@brief Rebuild the Core WAT tool from the selected SDK's locked sources without network access."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
VENDOR = HERE.parents[2] / "third-parties/wat-mte"


def build(source, rust_bin, output):
    """@brief Authenticate the source snapshot, apply the wire patch and build an offline release."""
    lock = json.loads((VENDOR / "release.json").read_bytes())
    if hashlib.sha256(source.read_bytes()).hexdigest() != lock["source_sha256"]:
        raise ValueError("locked WAT tool sources differ")
    rustc = (rust_bin / "rustc").resolve(strict=True)
    cargo = (rust_bin / "cargo").resolve(strict=True)
    if subprocess.check_output([rustc, "--version"], text=True).strip() != lock["rustc"]:
        raise ValueError("use the Rust release named by the WAT tool manifest")
    with tempfile.TemporaryDirectory(dir=output.resolve().parent) as directory:
        stage = Path(directory)
        with tarfile.open(source, "r:xz") as archive:
            archive.extractall(stage, filter="data")
        for name in ("Cargo.toml", "Cargo.lock"):
            shutil.copyfile(HERE / name, stage / name)
        shutil.copytree(HERE / "src", stage / "src")
        from extend import extend
        extend(stage / "vendor")
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "RUSTC": str(rustc),
               "CARGO_HOME": str(stage / "cargo-home"), "CARGO_INCREMENTAL": "0",
               "RUSTFLAGS": f"--remap-path-prefix={stage}=.",
               "SOURCE_DATE_EPOCH": "1"}
        subprocess.run([cargo, "build", "--locked", "--offline", "--release", "-j", "4"],
                       cwd=stage, env=env, check=True)
        tool = stage / "target/release/wros-wat-core"
        subprocess.run(["/usr/bin/strip", "--strip-debug", tool], check=True)
        with output.open("xb") as destination, tool.open("rb") as executable:
            shutil.copyfileobj(executable, destination)
        output.chmod(0o755)


def main():
    """@brief Build the SDK's pinned release into a new output file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(VENDOR / "sources.tar.xz", args.rust_bin, args.output)


if __name__ == "__main__":
    main()
