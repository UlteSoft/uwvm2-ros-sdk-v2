"""Build the SDK's native wrrs using the vendored rustc source and its official stage0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
SRC = HERE / "upstream"
sys.path.insert(0, str(HERE.parent))
from official_dist import fetch_archive
HOST = "x86_64-unknown-linux-gnu"


def stage0_lock():
    return dict(line.split("=", 1) for line in (SRC / "src/stage0").read_text().splitlines()
                if line and not line.startswith("#"))


def install_stage0(archives, work, cache):
    lock = stage0_lock()
    root = work / "stage0"
    # Always check the three official archives, even on a retry after a partial installation.
    with tempfile.TemporaryDirectory(dir=work) as directory:
        for component in ("rustc", "rust-std", "cargo"):
            name = f"{component}-{lock['compiler_version']}-{HOST}"
            filename = name + ".tar.xz"
            relative = f"dist/{lock['compiler_date']}/{filename}"
            archive = (archives / filename if archives else
                       fetch_archive("https://static.rust-lang.org/" + relative, lock[relative], cache))
            with archive.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != lock[relative]:
                    raise ValueError("official stage0 archive SHA-256 mismatch: " + archive.name)
                stream.seek(0)
                with tarfile.open(fileobj=stream, mode="r:xz") as tar:
                    tar.extractall(directory, filter="data")
            subprocess.run(["sh", Path(directory) / name / "install.sh", "--prefix=" + str(root),
                            "--disable-ldconfig"], check=True)
    return root / "bin"


def write_config(work, rust_bin):
    config = work / "bootstrap.toml"
    compiler = rust_bin / "rustc"
    cargo = rust_bin / "cargo"
    identity = subprocess.check_output([compiler, "-vV"], text=True).splitlines()
    lock = stage0_lock()
    if f"commit-hash: {lock['compiler_git_commit_hash']}" not in identity or f"host: {HOST}" not in identity:
        raise ValueError(f"expected official {HOST} rustc {lock['compiler_version']} and its host standard library")
    cargo_version = subprocess.check_output([cargo, "-V"], text=True).split()
    if cargo_version[:2] != ["cargo", lock["compiler_version"]]:
        raise ValueError(f"expected cargo {lock['compiler_version']} in the bootstrap bin directory")
    config.write_text(f"""change-id = "ignore"

[build]
build = "{HOST}"
host = ["{HOST}"]
target = ["{HOST}"]
rustc = {json.dumps(str(compiler))}
cargo = {json.dumps(str(cargo))}
build-dir = {json.dumps(str(work / "build"))}
vendor = true
submodules = false
extended = false
docs = false
compiler-docs = false
optimized-compiler-builtins = false

[llvm]
download-ci-llvm = false
ninja = true
link-shared = false
targets = "X86;WebAssembly"
experimental-targets = ""
tests = false
assertions = false
link-jobs = 1

[rust]
channel = "stable"
download-rustc = false
rpath = true
debug = false
debuginfo-level = 0
incremental = false
lto = "off"
lld = false
llvm-tools = false
llvm-bitcode-linker = false
deny-warnings = false
remap-debuginfo = true

[target.{HOST}]
default-linker-linux-override = "off"
""")
    return config


def needed(path):
    dynamic = subprocess.check_output(["readelf", "-dW", path], text=True)
    return re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", dynamic)


def publish_runtime(stage, prefix):
    # Stage1 may use a shared compiler and/or shared host std. Follow the native
    # loader dependencies, including indirect deps, to produce a relocatable pair.
    libdirs = (stage / "lib", stage / "lib/rustlib" / HOST / "lib")
    files = {"bin/wrrs": stage / "bin/rustc"}
    pending = list(files.values())
    seen = set()
    system = set()
    while pending:
        for name in needed(pending.pop()):
            if name in seen:
                continue
            seen.add(name)
            source = next((directory / name for directory in libdirs if (directory / name).is_file()), None)
            if source is not None:
                files["lib/" + name] = source
                pending.append(source)
            elif name.startswith(("librust", "libstd-", "libLLVM", "libcore-")):
                raise ValueError("stage1 does not contain compiler dependency " + name)
            else:
                system.add(name)
    with tempfile.TemporaryDirectory(dir=prefix) as directory:
        staging = Path(directory)
        for dest, source in files.items():
            target = staging / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            subprocess.run(["strip", "--strip-unneeded", target], check=True)
            target.chmod(0o755)
        os.link(staging / "bin/wrrs", staging / "bin/rustc")
        for item in [*files, "bin/rustc"]:
            target = prefix / item
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / item, target)
    return files, sorted(system)


def package_release(files, prefix, output, system):
    sys.path.insert(0, str(HERE.parent))
    from package_native import package

    packages, artifacts = {}, {}
    for path in sorted(files):
        if path == "bin/wrrs":
            key, targets = "wrrs", ["bin/wrrs", "bin/rustc"]
        else:
            key, targets = "wrrs-" + re.sub("[^a-z0-9+-]", "-", Path(path).name.lower()), [path]
        archive = output / (key + ".tar.xz")
        metadata = package(prefix / path, key, archive)
        immutable = output / (key + "-" + metadata["compressed_sha256"][:20] + ".tar.xz")
        os.replace(archive, immutable)
        packages[key] = dict(metadata, path=f"bin/packages/linux-x86_64/wrrs/{immutable.name}")
        artifacts[key] = targets
    descriptor = output / "rust-packages.json"
    descriptor.write_text(json.dumps(dict(packages=packages, artifacts=artifacts, system_libraries=system),
                                     indent=2, sort_keys=True) + "\n")
    print(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--prefix", required=True, type=Path, help="write bin/wrrs, bin/rustc and the compiler libraries")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stage0-archives", type=Path, help="use previously downloaded official rustc, rust-std and Cargo archives")
    group.add_argument("--rust-bin", type=Path, help="an installed official stage0 bin directory")
    parser.add_argument("--download-cache", type=Path, help="verified upstream distribution cache")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--packages", type=Path, help="also write verified single-ELF release archives and a manifest fragment")
    args = parser.parse_args()
    if sys.platform != "linux" or platform.machine().lower() not in ("amd64", "x86_64"):
        parser.error("the native wrrs source build currently targets x86-64 Linux")
    work, prefix = args.work.resolve(), args.prefix.resolve()
    if work.is_relative_to(SRC) or prefix.is_relative_to(SRC) or args.jobs < 1:
        parser.error("use positive --jobs and stage build artifacts outside the editable Rust source")
    work.mkdir(parents=True, exist_ok=True)
    prefix.mkdir(parents=True, exist_ok=True)
    temp = work / "tmp"
    temp.mkdir(exist_ok=True)
    os.environ.update(TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp), CARGO_HOME=str(work / "cargo-home"),
                      CARGO_NET_OFFLINE="true", RUSTUP_AUTO_INSTALL="0", PYTHONDONTWRITEBYTECODE="1",
                      SOURCE_DATE_EPOCH="1787011200", LC_ALL="C", TZ="UTC")
    if args.rust_bin:
        rust_bin = args.rust_bin.resolve()
    else:
        rust_bin = install_stage0(args.stage0_archives, work, args.download_cache or work / "downloads")
    config = write_config(work, rust_bin)
    subprocess.run([sys.executable, "-B", SRC / "x.py", "build", "--config", config, "--stage", "1",
                    "--jobs", str(args.jobs), "compiler/rustc"], cwd=SRC, check=True)
    files, system = publish_runtime(work / "build" / HOST / "stage1", prefix)
    if args.packages:
        target = args.packages.resolve()
        target.mkdir(parents=True, exist_ok=True)
        package_release(files, prefix, target, system)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        sys.exit(f"wrrs rebuild failed: {error}")
