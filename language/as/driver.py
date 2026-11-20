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
sys.path.insert(0, str(ROOT / "install"))
from artifacts import uleb
from imports import Reader, inspect, require_core

VENDOR = ROOT / "third-parties/assemblyscript"
RELEASE_SHA256 = "2485652b4d05b60a9f48afa0f3b42a897f3ab380cf40564f44923401e0d425b7"
SOURCE_LIMIT = 1024 * 1024
OUTPUT_LIMIT = 8 * 1024 * 1024
ABI = {"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}
DRIVER_OPERATIONS = {
    "capability.open": ["i32", "i64", "i64", "i64"],
    "capability.close": ["i64"],
    **{"driver." + name: ["i64", "i32", "i64", "i64", "i64", "i64", "i64"]
       for name in ("connect", "submit", "result", "describe", "disconnect")},
}
CLAIM_EXPORT = "__wros_as_claimz"
CLAIM_STUB = b"\x00\x20\x00\x0b"
CLAIM_BODY = b"\x00\x20\x00\x20\x01\xff" + uleb(0x01010041) + b"\x00\x0b"


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


def driver_wasm(data, tagged, selected):
    """@brief Check private staging and replace one compiler-owned body with managed claimz."""
    imports = inspect(data)
    names = set()
    for entry in imports:
        name = entry["name"]
        if (name not in DRIVER_OPERATIONS or name in names or
                entry != {"module": "uwvm_ros_v2", "name": name, "kind": 0,
                          "params": DRIVER_OPERATIONS[name], "results": ["i32"]}):
            raise ValueError("driver host imports must exactly match approved signatures")
        names.add(name)
    if selected and (len(selected) != len(set(selected)) or names != set(selected)):
        raise ValueError("driver host imports differ from the requested operations")

    source = Reader(data)
    require_core(source)
    module = [bytes(source.data[:8])]
    claim = None
    memory = False
    patched = False
    while source.position < len(data):
        start = source.position
        section = source.byte()
        body = Reader(source.take(source.uint()))
        replacement = None
        if section == 5:
            if memory or tuple(body.uint() for _ in range(4)) != (1, 1, 1, 1):
                raise ValueError("the driver profile requires exactly one private fixed wasm32 page")
            body.end()
            memory = True
        elif section in (11, 12):
            if body.uint() != 0:
                raise ValueError("the driver profile requires zero-initialized private buffers")
            body.end()
        elif section == 7:
            exports = []
            for _ in range(body.count()):
                offset = body.position
                name, kind, index = body.name(), body.byte(), body.uint()
                if kind == 2:
                    raise ValueError("the driver profile does not export its memory")
                if name == CLAIM_EXPORT:
                    if not tagged or claim is not None or kind != 0 or index < len(imports):
                        raise ValueError("invalid compiler-owned claim stub")
                    claim = index - len(imports)
                else:
                    exports.append(body.data[offset:body.position])
            body.end()
            if claim is not None:
                replacement = uleb(len(exports)) + b"".join(exports)
        elif section == 10 and tagged:
            count = body.count()
            if claim is None or claim >= count:
                raise ValueError("invalid compiler-owned claim function index")
            functions = [uleb(count)]
            for index in range(count):
                code = body.take(body.uint())
                if index == claim:
                    if code != CLAIM_STUB:
                        raise ValueError("the compiler-owned claim stub changed")
                    code, patched = CLAIM_BODY, True
                functions.extend((uleb(len(code)), code))
            body.end()
            replacement = b"".join(functions)
        if replacement is None:
            module.append(source.data[start:source.position])
        else:
            module.extend((bytes([section]), uleb(len(replacement)), replacement))
    if not memory or patched != tagged:
        raise ValueError("incomplete driver profile")
    return b"".join(module), names


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
        helpers = ["compile.mjs"]
        flags = ["--debug"] if args.debug else []
        if args.ros_driver:
            helpers.extend(("driver_lowering.mjs", "wros.ts"))
            flags.append("--driver")
            if not args.mte:
                flags.append("--plain")
        for helper in helpers:
            shutil.copyfile(Path(__file__).with_name(helper), stage / helper)
        subprocess.run([node, "compile.mjs", *flags], cwd=stage,
                       env={"HOME": str(stage), "LC_ALL": "C", "PATH": "/nonexistent"},
                       timeout=60, check=True)
        guest = stage / "result.wasm"
        with guest.open("rb") as stream:
            data = stream.read(OUTPUT_LIMIT + 1)
        if not 0 < len(data) <= OUTPUT_LIMIT:
            raise ValueError("emitted Wasm exceeds the output budget")
        if args.ros_driver:
            data, names = driver_wasm(data, args.mte, args.ros_operation)
            if len(data) > OUTPUT_LIMIT:
                raise ValueError("tagged driver Wasm exceeds the output budget")
            guest.write_bytes(data)
        else:
            check_output(data, args.ros_abi)
            names = {"abi"} if args.ros_abi else set()
        sidecar = Path(str(output) + ".wros-as.json")
        if args.build_receipt:
            proof = stage / "build.json"
            proof.write_text(json.dumps({
                "language": "as", "profile": "bounded-driver-wasm32" if args.ros_driver else "register-only-wasm32",
                "compiler_release_sha256": RELEASE_SHA256, "mte_requested": args.mte,
                "linear_memories": int(args.ros_driver), "wasm_sha256": hashlib.sha256(data).hexdigest(),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "wasm_imports": ["uwvm_ros_v2." + name for name in sorted(names)],
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ros-abi", action="store_true")
    mode.add_argument("--ros-driver", action="store_true")
    parser.add_argument("--ros-operation", action="append", choices=DRIVER_OPERATIONS, default=[])
    parser.add_argument("--build-receipt", action="store_true")
    parser.add_argument("-g", dest="debug", action="store_true")
    args = parser.parse_args()
    if args.ros_operation and not args.ros_driver:
        parser.error("--ros-operation requires --ros-driver")
    try:
        build(args)
    except (OSError, KeyError, TypeError, ValueError, lzma.LZMAError, tarfile.TarError,
            subprocess.SubprocessError) as error:
        parser.exit(1, f"wras: {error}\n")


if __name__ == "__main__":
    main()
