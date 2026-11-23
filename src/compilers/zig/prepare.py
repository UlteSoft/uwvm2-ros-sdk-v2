"""Install the Zig standard library, or rebuild wrzig and its LLVM storage pass."""
import argparse
from hashlib import file_digest
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rebuild import build_frontend, build_marker
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from official_dist import fetch_archive


def unpack(archive, destination, *, bootstrap):
    release = "zig-x86_64-linux-0.16.0"
    # Match the official release index recorded with the editable source.
    upstream = json.loads(Path(__file__).with_name("upstream.json").read_bytes())["bootstrap"]
    with archive.open("rb") as stream:
        if archive.stat().st_size != upstream["bytes"] or file_digest(stream, "sha256").hexdigest() != upstream["sha256"]:
            raise ValueError("Zig bootstrap archive differs from the pinned upstream release")
    with tarfile.open(archive, "r|xz") as source:
        for member in source:
            name = PurePosixPath(member.name)
            if name.is_absolute() or not name.parts or name.parts[0] != release or ".." in name.parts:
                raise ValueError("invalid Zig release archive path")
            if member.isdir():
                continue
            if not member.isfile() or len(name.parts) < 2:
                raise ValueError("unexpected file type in the Zig release archive")
            first = name.parts[1]
            if first not in {"lib", "LICENSE"} and not (bootstrap and name.parts[1:] == ("zig",)):
                continue
            target = destination.joinpath(*name.parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as contents, target.open("xb") as output:
                shutil.copyfileobj(contents, output)
            target.chmod(0o755 if first == "zig" else 0o644)


def build_llvm_marker(sdk, work, jobs):
    source = sdk / "src/compilers/cc/llvm-project/llvm"
    build = work / "zig-marker-llvm"
    env = dict(os.environ, TMPDIR=str(work))
    subprocess.run(["cmake", "-G", "Ninja", "-S", source, "-B", build, "-DCMAKE_BUILD_TYPE=Release",
                    "-DLLVM_TARGETS_TO_BUILD=WebAssembly", "-DLLVM_INCLUDE_TESTS=OFF",
                    "-DLLVM_INCLUDE_EXAMPLES=OFF", "-DLLVM_INCLUDE_BENCHMARKS=OFF",
                    "-DLLVM_ENABLE_PROJECTS=", "-DLLVM_ENABLE_ZLIB=OFF", "-DLLVM_ENABLE_ZSTD=OFF",
                    "-DLLVM_ENABLE_LIBXML2=OFF", "-DLLVM_ENABLE_LIBEDIT=OFF", "-DLLVM_ENABLE_TERMINFO=OFF",
                    "-DLLVM_ENABLE_BINDINGS=OFF", "-DLLVM_APPEND_VC_REV=OFF"],
                   check=True, env=env)
    subprocess.run(["cmake", "--build", build, "--parallel", str(jobs), "--target", "llvm-config",
                    "LLVMBitWriter", "LLVMIRReader", "LLVMCore"], check=True, env=env)
    build_marker(sdk / "src/compilers/zig/mark_mte.cpp", build / "bin/llvm-config",
                 os.environ.get("CXX", "c++"), sdk / "share/toolchains/zig/bin/wros-zig-mte", work)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sdk", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--mode", choices=("source", "binary"), required=True)
    p.add_argument("--jobs", type=int, default=2)
    a = p.parse_args()
    sdk, work = a.sdk.resolve(), a.work.resolve()
    native = sdk / "share/toolchains/zig"
    release = json.loads((sdk / "src/compilers/zig/upstream.json").read_bytes())["bootstrap"]
    archive = fetch_archive(release["url"], release["sha256"], os.environ.get("WROS_DIST_CACHE", work / "downloads"), size=release["bytes"])
    if a.mode == "binary":
        unpack(archive, native, bootstrap=False)
    else:
        producer = work / "zig-bootstrap"
        unpack(archive, producer, bootstrap=True)
        source = sdk / "src/compilers/zig/upstream"
        # Source installs use and expose the standard library from the checkout.
        shutil.copytree(source / "lib", native / "lib", copy_function=os.link)
        shutil.copy2(source / "LICENSE", native / "LICENSE")
        build_frontend(source, producer / "zig", sdk / "bin/wrzig", work / "zig-frontend", a.jobs)
        build_llvm_marker(sdk, work, a.jobs)


if __name__ == "__main__":
    main()
