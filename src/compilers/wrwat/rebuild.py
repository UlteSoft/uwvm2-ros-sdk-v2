"""Rebuild the native Core WAT tool offline from the inputs in a WAT source selection."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import sys
import shutil
import subprocess
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
SDK = HERE.parents[2]
PACKER = runpy.run_path(str(HERE.parent / "package_native.py"))
INSTALLER = PACKER["INSTALLER"]
sys.path.insert(0, str(HERE.parent))
from official_dist import fetch_archive

GNU_X86_64 = "linux-x86_64"
LLVM_COMMIT = "52ed14fcd56afc30f9cccd8ca8ce237c2eef7e04"


def check_linker(identity):
    # The official 32-bit ARM builds name the upstream URL here, other hosts use a checkout path.
    if not re.fullmatch(rf"LLD 22\.1\.8 \([^()]+ {LLVM_COMMIT}\)", identity):
        raise ValueError(f"unexpected Rust ELF linker: {identity}")
    return identity


def bootstrap_lock(host):
    if host not in INSTALLER["HOSTS"]:
        raise ValueError(f"unsupported Linux build ABI: {host}")
    path = HERE / "bootstrap.json" if host == GNU_X86_64 else HERE / "bootstrap" / (host + ".json")
    return json.loads(path.read_bytes())


def unpack_component(component, root, cache):
    """Install only the regular files named by the release lock into a private prefix."""
    archive = fetch_archive(component["url"], component["compressed_sha256"], cache, size=component["compressed_bytes"])
    prefix = component["member_prefix"]
    remaining = dict(component["files"])
    with archive.open("rb") as source:
        if (os.fstat(source.fileno()).st_size != component["compressed_bytes"] or
                hashlib.file_digest(source, "sha256").hexdigest() != component["compressed_sha256"]):
            raise ValueError(f"Rust archive failed verification: {archive.name}")
        source.seek(0)
        with tarfile.open(fileobj=source, mode="r|xz") as tar:
            for member in tar:
                if not member.name.startswith(prefix):
                    continue
                relative = member.name[len(prefix):]
                if relative not in component["files"]:
                    continue
                path = PurePosixPath(relative)
                meta = remaining.pop(relative, None)
                if (meta is None or path.is_absolute() or ".." in path.parts or str(path) != relative or
                        member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE) or member.linkname or
                        member.size != meta["bytes"] or member.mode != int(meta["mode"], 8)):
                    raise ValueError(f"Unexpected Rust archive member: {member.name}")
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with tar.extractfile(member) as src, dest.open("xb") as out:
                    while block := src.read(1024 * 1024):
                        digest.update(block)
                        out.write(block)
                if digest.hexdigest() != meta["sha256"]:
                    raise ValueError(f"Rust member failed SHA-256 verification: {member.name}")
                dest.chmod(member.mode)
    if remaining:
        raise ValueError(f"Missing Rust files in {archive.name}: {', '.join(remaining)}")


def publish_program(tool, output):
    tool.chmod(0o755)
    try:
        os.link(tool, output)
        return
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
    with output.open("xb") as destination:
        try:
            with tool.open("rb") as source:
                shutil.copyfileobj(source, destination)
            destination.flush()
            os.fchmod(destination.fileno(), 0o755)
        except BaseException:
            output.unlink()
            raise


def build(rust_bin, output, *, host=None, work=None, jobs=4, cache=None):
    """Use tools executable on the build machine and the standard library for the selected target."""
    builder = INSTALLER["current_host"]()
    host = host or builder
    bootstrap = bootstrap_lock(builder)
    target_lock = bootstrap_lock(host)
    if host == GNU_X86_64 and builder != host:
        raise ValueError("the GNU x86-64 release needs the native x86-64 cc and glibc development files")
    if jobs < 1:
        raise ValueError("--jobs must be positive")
    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    work = (work or SDK / ".tmp").resolve()
    work.mkdir(parents=True, exist_ok=True)
    cache = cache or work / "downloads"
    with tempfile.TemporaryDirectory(dir=work, prefix="wrwat-") as directory:
        stage = Path(directory)
        if rust_bin is None:
            prefix = stage / "rust"
            for name in ("rustc", "cargo", "rust-std"):
                unpack_component(bootstrap["components"][name], prefix, cache)
            rust_bin = prefix / "bin"
        rustc = (rust_bin / "rustc").absolute()
        cargo = (rust_bin / "cargo").absolute()
        identity = subprocess.check_output([rustc, "-vV"], text=True).splitlines()
        rust_version = "rustc " + bootstrap["components"]["rustc"]["package_version"]
        rust_host = next((line.removeprefix("host: ") for line in identity if line.startswith("host: ")), None)
        native_hosts = {bootstrap["host"]}
        if bootstrap.get("target_has_official_host_tools"):
            native_hosts.add(bootstrap["target"])
        if (rust_version not in identity or f"commit-hash: {bootstrap['rust_commit']}" not in identity
                or rust_host not in native_hosts):
            raise ValueError(f"expected {rust_version} for {', '.join(sorted(native_hosts))}")
        if subprocess.check_output([cargo, "--version"], text=True).strip() != bootstrap["cargo"]:
            raise ValueError(f"expected {bootstrap['cargo']}")

        (stage / "tmp").mkdir()
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "RUSTC": str(rustc), "TMPDIR": str(stage / "tmp"),
               "CARGO_HOME": str(stage / "cache/cargo"), "CARGO_TARGET_DIR": str(stage / "build"),
               "CARGO_INCREMENTAL": "0", "SOURCE_DATE_EPOCH": "1"}
        command = [cargo, "build", "--locked", "--offline", "--release", "-j", str(jobs)]
        if host == GNU_X86_64:
            flags = [f"--remap-path-prefix={stage}=.", f"--remap-path-prefix={HERE}=."]
            tool = stage / "build/release/wrwat"
        else:
            target = target_lock["target"]
            sysroot = stage / "toolchain"
            unpack_component(target_lock["target_std"], sysroot, cache)
            native = Path(subprocess.check_output([rustc, "--print", "sysroot"], text=True).strip())
            rustlib = native / "lib/rustlib" / rust_host
            if target != rust_host:
                (sysroot / "lib/rustlib" / rust_host).symlink_to(rustlib, target_is_directory=True)
            linker = rustlib / "bin/rust-lld"
            version = subprocess.check_output([linker, "-flavor", "gnu", "--version"], text=True).strip()
            check_linker(version.removesuffix(" (compatible with GNU linkers)"))
            # Keep the release's file!() paths for Cargo's vendored registry sources.
            flags = [f"--sysroot={sysroot}", "-C", f"linker={linker}", "-C", "linker-flavor=ld.lld",
                     "-C", "link-self-contained=yes", "-C", "strip=debuginfo",
                     f"--remap-path-prefix={HERE}=./sources/wrwat", f"--remap-path-prefix={stage}=."]
            command.extend(["--target", target])
            tool = stage / "build" / target / "release/wrwat"
        env["CARGO_ENCODED_RUSTFLAGS"] = "\x1f".join(flags)
        subprocess.run(command, cwd=HERE, env=env, check=True)
        if host == GNU_X86_64:
            subprocess.run(["/usr/bin/strip", "--strip-debug", tool], check=True)
        INSTALLER["require_host"](tool, host)
        publish_program(tool, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=INSTALLER["HOSTS"], help="SDK ABI of the output (default: this Linux ABI)")
    parser.add_argument("--rust-bin", type=Path, help="use a matching official host rustc, Cargo and host std")
    parser.add_argument("--work", type=Path, help="writable scratch directory (default: SDK .tmp)")
    parser.add_argument("--download-cache", type=Path, help="verified upstream distribution cache")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.rust_bin, args.output, host=args.host, work=args.work, jobs=args.jobs, cache=args.download_cache)


if __name__ == "__main__":
    main()
