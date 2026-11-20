"""@file driver.py
@brief Assemble WAT and validate the selected core features and exact ROS imports.
"""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import sections
from imports import inspect

VENDOR = ROOT / "third-parties/wat-mte"
TOOL_LIMIT = 32 << 20
SOURCE_LIMIT = 8 << 20
MODULE_LIMIT = 64 << 20


def read(path, limit):
    """@brief Take one bounded snapshot of an input file."""
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError(f"{path.name} must contain between 1 and {limit} bytes")
    return data


def assembler(stage):
    """@brief Check and stage the digest-bound Core-only assembler and validator."""
    release = json.loads(read(VENDOR / "release.json", 16 << 10))
    package = read(VENDOR / "wros-wat-core-linux-x86_64.xz", TOOL_LIMIT)
    if hashlib.sha256(package).hexdigest() != release["compressed_sha256"]:
        raise ValueError("WAT assembler archive differs from the pinned release")
    if not 0 < release["binary_bytes"] <= TOOL_LIMIT:
        raise ValueError("unexpected WAT assembler size")
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128 << 20)
    binary = decoder.decompress(package, max_length=release["binary_bytes"] + 1)
    if (not decoder.eof or decoder.unused_data or len(binary) != release["binary_bytes"]
            or hashlib.sha256(binary).hexdigest() != release["binary_sha256"]):
        raise ValueError("WAT assembler differs from the pinned release")
    executable = stage / "wros-wat-core"
    executable.write_bytes(binary)
    executable.chmod(0o700)
    return executable, release["binary_sha256"]


def features(args):
    """@brief Select the standard core grammar and only explicitly chosen extensions."""
    if args.core == "mvp":
        if args.target != "wasm32" or args.eh or args.threads:
            raise ValueError("MVP requires wasm32 without EH or threads")
        return "mvp"
    flags = ["wasm3", "-component-model", "-legacy-exceptions"]
    flags.append("threads" if args.threads else "-threads")
    if args.target == "wasm32":
        flags.append("-memory64")
    if args.eh is False:
        flags.append("-exceptions")
    if args.mte:
        flags.append("memtag-extension")
    return ",".join(flags)


def check_shared_memory(data, target):
    """@brief Check one explicitly selected, bounded shared owner import."""
    for offset, _, _, body in sections(data):
        if data[offset] != 2:
            continue
        for _ in range(body.count()):
            body.name()
            body.name()
            kind = body.byte()
            if kind == 0:
                body.uint()
                continue
            flags = body.uint()
            if flags != (7 if target == "wasm64" else 3):
                raise ValueError("selected owner must be a bounded shared memory of the configured address width")
            bits = 64 if flags & 4 else 32
            body.uint(bits)
            body.uint(bits)
        body.end()


def check_module(data, args):
    """@brief Require exact host imports and distinguish explicit MTE from a memory-free build."""
    catalogue = json.loads((ROOT / "share/abi/ros.json").read_bytes())
    signatures = {row["name"]: row["wasm_signature"] for row in catalogue["operations"]}
    selected = set(args.ros_operation)
    if len(selected) != len(args.ros_operation) or not selected <= signatures.keys():
        raise ValueError("select distinct operations from the installed ROSv2 catalogue")
    imports = inspect(data)
    seen = set()
    memory = None
    spawn = False
    for row in imports:
        if row["kind"] == 2 and args.threads and [row["module"], row["name"]] == args.shared_memory and memory is None:
            memory = (row["module"], row["name"])
            continue
        if (args.threads and args.target == "wasm32" and not spawn
                and row == {"module": "wasi", "name": "thread-spawn", "kind": 0,
                            "params": ["i32"], "results": ["i32"]}):
            spawn = True
            continue
        signature = signatures.get(row["name"])
        if (row["module"] != catalogue["module"] or row["kind"] != 0 or row["name"] not in selected
                or row["name"] in seen
                or signature != {"parameters": row["params"], "results": row["results"]}):
            raise ValueError(f"unauthorized import or signature {row['module']}.{row['name']}")
        seen.add(row["name"])
    if seen != selected:
        raise ValueError("the module must import each selected ROSv2 operation exactly once")
    if args.shared_memory and memory is None:
        raise ValueError("expected exactly one declared shared memory import")
    if memory is not None:
        check_shared_memory(data, args.target)
    if spawn and memory is None:
        raise ValueError("thread-spawn requires an explicitly selected shared memory owner")
    memory_free = memory is None and not any(data[offset] in (5, 11, 12) and body.uint()
                                              for offset, _, _, body in sections(data))
    return memory_free, spawn


def build(args):
    """@brief Publish only a complete validated core module and an optional build receipt."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise ValueError("the bundled WAT assembler requires a Linux x86-64 build host")
    if args.source.suffix != ".wat" or args.output.suffix != ".wasm":
        raise ValueError("use a .wat source and a .wasm output")
    flags = features(args)
    source = read(args.source, SOURCE_LIMIT)
    if source.startswith(b"\0asm"):
        raise ValueError("wrwat expects text input")
    source.decode("utf-8", errors="strict")
    output = args.output.absolute()
    with tempfile.TemporaryDirectory(dir=output.parent) as name:
        stage = Path(name)
        tool, tool_digest = assembler(stage)
        (stage / args.source.name).write_bytes(source)
        guest = stage / "guest.wasm"
        environment = {"LC_ALL": "C", "PATH": "/nonexistent"}
        switches = ["on" if value else "off" for value in
                    (args.core == "3.0" and args.eh is not False, args.threads, args.mte, args.debug)]
        result = subprocess.run([tool, args.source.name, guest, args.core, args.target, *switches],
                                cwd=stage, env=environment, timeout=60, check=True, stdout=subprocess.PIPE)
        data = read(guest, MODULE_LIMIT)
        tag_writes = int(result.stdout)
        memory_free, spawn = check_module(data, args)
        sidecar = output.with_suffix(".wasm.wros-wat.json")
        if args.build_receipt:
            proof = stage / "receipt.json"
            proof.write_text(json.dumps({
                "language": "wat", "target": args.target, "validation_features": flags,
                "mte_requested": args.mte, "linear_memory_free": memory_free,
                "authored_tag_writes": tag_writes, "shared_memory": args.shared_memory, "thread_spawn": spawn,
                "ros_operations": sorted(args.ros_operation),
                "assembler_sha256": tool_digest,
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "wasm_sha256": hashlib.sha256(data).hexdigest(),
            }, indent=2) + "\n")
            os.replace(proof, sidecar)
        else:
            sidecar.unlink(missing_ok=True)
        os.replace(guest, output)


def main():
    """@brief Accept the SDK's closed WAT assembly options."""
    cli = argparse.ArgumentParser(prog="wrwat", description="Assemble and validate a core WebAssembly text module")
    cli.add_argument("source", type=Path)
    cli.add_argument("-o", "--output", required=True, type=Path)
    cli.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    cli.add_argument("--core", choices=("mvp", "3.0"), default="3.0")
    cli.add_argument("--eh", action=argparse.BooleanOptionalAction)
    cli.add_argument("--threads", action="store_true")
    cli.add_argument("--shared-memory", nargs=2, metavar=("MODULE", "FIELD"),
                     help="select one named shared memory import in a threaded module")
    cli.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    cli.add_argument("--ros-operation", action="append", default=[])
    cli.add_argument("--build-receipt", action="store_true")
    cli.add_argument("-g", dest="debug", action="store_true")
    args = cli.parse_args()
    try:
        build(args)
    except (OSError, ValueError, KeyError, lzma.LZMAError, subprocess.SubprocessError) as error:
        cli.exit(1, f"wrwat: {error}\n")


if __name__ == "__main__":
    main()
