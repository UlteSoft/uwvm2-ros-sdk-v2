"""Build one freestanding Odin program to audited wasm32 Core Wasm."""
import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))

from artifacts import read_bounded, unique_object
from compiler import compiler_environment, digest, make_command
from frontend import audit
from guest_profile import Profile
from imports import inspect
from local_release import read_file
from qualification import finish

VENDOR = ROOT / "third-parties/odin"
RELEASE_SHA256 = "d73aaa13d945203a7d269c0c7a3bf1f723efa6ef6ca2b810f73d66232ffa94ce"
PRODUCER = {"odin", "wros-odin-mte"}
ABI = {"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}


def unpack(work):
    """Verify the source-built host producer and extract its bounded file set."""
    lock = read_file(VENDOR / "release.json", 8192)
    if sha256(lock).hexdigest() != RELEASE_SHA256:
        raise ValueError("unexpected Odin producer manifest")
    release = json.loads(lock, object_pairs_hook=unique_object)
    archive = read_file(VENDOR / "producer.tar.xz", 32 << 20)
    if len(archive) != release["archive_bytes"] or sha256(archive).hexdigest() != release["archive_sha256"]:
        raise ValueError("Odin producer archive differs from the release manifest")
    producer = work / "producer"
    for name in ("base", "core", "shared", "vendor"):
        (producer / name).mkdir(parents=True, exist_ok=True)
    total = 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as package:
        for member in package:
            path = PurePosixPath(member.name)
            if (not path.parts or path.is_absolute() or ".." in path.parts or not member.isfile() or
                    (path.parts[0] not in ("base",) and member.name not in PRODUCER)):
                raise ValueError("unexpected Odin producer file")
            total += member.size
            if total > release["unpacked_bytes"]:
                raise ValueError("Odin files exceed the release bound")
            destination = producer.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with package.extractfile(member) as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target)
            if member.name in PRODUCER:
                destination.chmod(0o700)
    if total != release["unpacked_bytes"] or not all((producer / name).is_file() for name in PRODUCER):
        raise ValueError("incomplete Odin producer archive")
    return producer, release


def build(args):
    """Link audited core Wasm and publish the artifact from private staging."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise ValueError("the bundled Odin host producer requires Linux x86-64")
    if args.source.suffix != ".odin" or args.output.suffix != ".wasm":
        raise ValueError("expected a .odin source and a separate .wasm output")
    if args.toolchain is None or not args.sysroots:
        raise ValueError("provide --toolchain and the matching --sysroots profile")
    original = args.source.resolve(strict=True)
    source = read_file(original, 1 << 20)
    source.decode("utf-8", errors="strict")
    profile = Profile(exceptions="noeh", mte=args.mte)
    tools = args.toolchain.resolve(strict=True)
    output = args.output.absolute()
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        work = Path(directory)
        producer, release = unpack(work)
        env = compiler_environment(tools)
        env.update(HOME=str(work), ODIN_ROOT=str(producer), TMPDIR=str(work))
        app = work / "application.odin"
        app.write_bytes(source)
        ir = work / "ir"
        ir.mkdir()
        marked, obj, module = (work / name for name in ("application.bc", "application.o", "application.wasm"))

        def run(command):
            subprocess.run(command, cwd=work, env=env, stdin=subprocess.DEVNULL, check=True, timeout=120)

        run([producer / "odin", "build", app, "-file", "-target:freestanding_wasm32", "-build-mode:llvm-ir",
             "-no-entry-point", "-no-crt", "-no-rtti", "-default-to-nil-allocator", "-debug", "-o:none", "-out:" + str(ir)])
        files = list(ir.glob("*.ll"))
        if len(files) != 1:
            raise ValueError("expected one LLVM IR module from one Odin source file")
        run([producer / "wros-odin-mte", "32", "on" if args.mte else "off", files[0], marked, original])
        command, closure = make_command(tools, args.sysroots, profile, "c",
                                        ["-O3", "-g", "-Wno-override-module", "-c", str(marked), "-o", str(obj)],
                                        verify=True)
        run(command)
        linker = tools / "bin/wasm-ld"
        run([linker, "--no-entry", "--export=_start", "--max-memory=16777216", obj, "-o", module])
        data = read_bounded(module)
        audit(data, profile)
        if inspect(data) != ([ABI] if args.ros_abi else []):
            raise ValueError("Odin guest must import precisely the selected ROSv2 ABI function, or nothing")
        finish({"format": "wros-odin-freestanding-development-v1", "language": "odin",
                "mode": "instrumented" if args.mte else "off", "profile": profile.to_dict(),
                "source_sha256": sha256(source).hexdigest(), "producer_release_sha256": RELEASE_SHA256,
                "upstream_revision": release["upstream_revision"], "compiler_sha256": closure["compiler_sha256"],
                "sysroot_sha256": closure["closure_sha256"], "linker_sha256": digest(linker),
                "authority_grants": []}, args, module, output)


def main():
    parser = argparse.ArgumentParser(prog="wrodin", description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--target", choices=("wasm32",), default="wasm32")
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--sysroots", action="append", type=Path)
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ros-abi", action="store_true")
    parser.add_argument("--build-receipt", action="store_true")
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError) as error:
        parser.exit(1, f"wrodin: {error}\n")


if __name__ == "__main__":
    main()
