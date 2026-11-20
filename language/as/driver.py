"""@file driver.py
@brief Build and verify the AssemblyScript scalar Wasm profile."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from install.imports import Reader, inspect, require_core

VENDOR = ROOT / "third-parties/assemblyscript"
RELEASE_SHA256 = "2485652b4d05b60a9f48afa0f3b42a897f3ab380cf40564f44923401e0d425b7"
SOURCE_LIMIT = 1024 * 1024
OUTPUT_LIMIT = 8 * 1024 * 1024
ABI = {"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}


def digest(path):
    """@brief Hash a file without loading it all into memory."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            result.update(block)
    return result.hexdigest()


def unpack_compiler(stage, lock):
    """@brief Start an exact release using a private fixed-layout staging directory."""
    bundle = VENDOR / "compiler.tar.xz"
    if not (0 < lock["uncompressed_bytes"] <= 32 << 20 and
            bundle.stat().st_size == lock["compressed_bytes"] and
            digest(bundle) == lock["compiler_sha256"]):
        raise ValueError("AssemblyScript compiler release differs from its manifest")
    count = 0
    with tarfile.open(bundle, "r:xz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            parts = path.parts
            if (len(parts) < 3 or parts[0] != "node_modules"
                    or parts[1] not in ("assemblyscript", "binaryen", "long")
                    or ".." in parts or not member.isfile()):
                raise ValueError("unexpected compiler bundle member")
            count += member.size
            if count > lock["uncompressed_bytes"]:
                raise ValueError("compiler bundle exceeds its expected size")
            target = stage.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    node_info = lock["node"]
    packed_node = ROOT / "third-parties/typescript/node-linux-x64.xz"
    if (not 0 < node_info["node_bytes"] <= 128 << 20
            or digest(packed_node) != node_info["node_xz_sha256"]):
        raise ValueError("host executable package differs from its manifest")
    node = stage / "node"
    with lzma.open(packed_node, "rb") as source, node.open("xb") as output:
        remaining = node_info["node_bytes"]
        while remaining:
            chunk = source.read(min(1 << 20, remaining))
            if not chunk:
                raise ValueError("truncated host executable")
            output.write(chunk)
            remaining -= len(chunk)
        if source.read(1):
            raise ValueError("oversized host executable")
    if digest(node) != node_info["node_binary_sha256"]:
        raise ValueError("host executable differs from its manifest")
    node.chmod(0o700)
    return node


def check_output(data, ros_abi):
    """@brief Verify the core module's lack of memory and exact optional host import."""
    if inspect(data) != ([ABI] if ros_abi else []):
        raise ValueError("the module must import precisely the selected ROSv2 abi function, or nothing")
    reader = Reader(data)
    require_core(reader)
    while reader.position < len(reader.data):
        section = reader.byte()
        body = reader.take(reader.uint())
        if section in (5, 11, 12):
            vector = Reader(body)
            if vector.uint() != 0:
                raise ValueError("linear memory and data are outside the scalar profile")
            vector.end()


def build(args):
    """@brief Publish a verified core Wasm binary after actual upstream compilation."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise ValueError("the bundled AssemblyScript build host requires Linux x86-64")
    if args.source.suffix != ".ts" or args.output.suffix != ".wasm":
        raise ValueError("use a .ts source and a .wasm output")
    with args.source.open("rb") as stream:
        source = stream.read(SOURCE_LIMIT + 1)
    if not 0 < len(source) <= SOURCE_LIMIT:
        raise ValueError("AssemblyScript source size must be between 1 byte and 1 MiB")
    source.decode("utf-8", errors="strict")
    profile = VENDOR / "release.json"
    if digest(profile) != RELEASE_SHA256:
        raise ValueError("unrecognized AssemblyScript compiler release")
    lock = json.loads(profile.read_bytes())
    output = args.output.absolute()
    with tempfile.TemporaryDirectory(dir=output.parent) as name:
        stage = Path(name)
        node = unpack_compiler(stage, lock)
        (stage / "input.ts").write_bytes(source)
        shutil.copyfile(Path(__file__).with_name("compile.mjs"), stage / "compile.mjs")
        subprocess.run([node, "compile.mjs", *(["--debug"] if args.debug else [])], cwd=stage,
                       env={"HOME": str(stage), "LC_ALL": "C", "PATH": "/nonexistent"},
                       timeout=60, check=True)
        guest = stage / "result.wasm"
        with guest.open("rb") as stream:
            data = stream.read(OUTPUT_LIMIT + 1)
        if not 0 < len(data) <= OUTPUT_LIMIT:
            raise ValueError("emitted Wasm exceeds the output budget")
        check_output(data, args.ros_abi)
        sidecar = Path(str(output) + ".wros-as.json")
        if args.build_receipt:
            proof = stage / "build.json"
            proof.write_text(json.dumps({
                "language": "as", "profile": "register-only-wasm32",
                "compiler_release_sha256": RELEASE_SHA256, "mte_requested": args.mte,
                "linear_memories": 0, "wasm_sha256": hashlib.sha256(data).hexdigest(),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "wasm_imports": ["uwvm_ros_v2.abi"] if args.ros_abi else [],
            }, indent=2) + "\n")
            os.replace(proof, sidecar)
        else:
            sidecar.unlink(missing_ok=True)
        os.replace(guest, output)


def main():
    """@brief Accept the wasm32 scalar options used by the SDK and Xmake."""
    parser = argparse.ArgumentParser(prog="wras", description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--target", choices=("wasm32",), default="wasm32")
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ros-abi", action="store_true")
    parser.add_argument("--build-receipt", action="store_true")
    parser.add_argument("-g", dest="debug", action="store_true")
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, KeyError, TypeError, ValueError, lzma.LZMAError, tarfile.TarError,
            subprocess.SubprocessError) as error:
        parser.exit(1, f"wras: {error}\n")


if __name__ == "__main__":
    main()
