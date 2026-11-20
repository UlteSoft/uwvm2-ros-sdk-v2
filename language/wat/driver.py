"""@file driver.py
@brief Assemble WAT and validate the selected core features and exact ROS imports.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import sections
from imports import inspect

RELEASE = "wasm-tools-1.263.0-x86_64-linux"
ARCHIVE_SIZE = 5976062
ARCHIVE_SHA256 = "21c036c1740a0552124c79c6e2170cb61c5b016005671a6d5bc06cf642165431"
TOOL_SIZE = 20539744
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
    """@brief Check the release and copy only its assembler/validator executable."""
    package = read(ROOT / "third-parties/wasm-tools" / (RELEASE + ".tar.gz"), ARCHIVE_SIZE)
    if hashlib.sha256(package).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("wasm-tools archive differs from the pinned release")
    executable = stage / "wasm-tools"
    with tarfile.open(fileobj=io.BytesIO(package), mode="r:gz") as archive:
        tool = archive.getmember(RELEASE + "/wasm-tools")
        if not tool.isfile() or tool.size != TOOL_SIZE:
            raise ValueError("missing or unexpected executable in the wasm-tools release")
        with archive.extractfile(tool) as source, executable.open("xb") as output:
            shutil.copyfileobj(source, output)
    executable.chmod(0o700)
    return executable


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
    return ",".join(flags)


def check_module(data, args):
    """@brief Require explicit, signature-exact ROS imports and prove memory absence for MTE."""
    catalogue = json.loads((ROOT / "share/abi/ros.json").read_bytes())
    signatures = {row["name"]: row["wasm_signature"] for row in catalogue["operations"]}
    selected = set(args.ros_operation)
    if len(selected) != len(args.ros_operation) or not selected <= signatures.keys():
        raise ValueError("select distinct operations from the installed ROSv2 catalogue")
    imports = inspect(data)
    for row in imports:
        signature = signatures.get(row["name"])
        if (row["module"] != catalogue["module"] or row["kind"] != 0 or row["name"] not in selected
                or signature != {"parameters": row["params"], "results": row["results"]}):
            raise ValueError(f"unauthorized import or signature {row['module']}.{row['name']}")
    if len(imports) != len(selected) or {row["name"] for row in imports} != selected:
        raise ValueError("the module must import each selected ROSv2 operation exactly once")
    memory_free = not any(data[offset] in (5, 11, 12) and body.uint() for offset, _, _, body in sections(data))
    if args.mte and not memory_free:
        raise ValueError("default MTE requires no linear memory or data segments; use --no-mte for raw memory")
    return memory_free


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
        tool = assembler(stage)
        (stage / args.source.name).write_bytes(source)
        guest = stage / "guest.wasm"
        environment = {"LC_ALL": "C", "PATH": "/nonexistent"}
        subprocess.run([tool, "parse", *(["-g"] if args.debug else []), "-o", guest, "--", args.source.name],
                       cwd=stage, env=environment, timeout=60, check=True)
        data = read(guest, MODULE_LIMIT)
        memory_free = check_module(data, args)
        subprocess.run([tool, "validate", "--features=" + flags, guest], cwd=stage,
                       env=environment, timeout=60, check=True)
        sidecar = output.with_suffix(".wasm.wros-wat.json")
        if args.build_receipt:
            proof = stage / "receipt.json"
            proof.write_text(json.dumps({
                "language": "wat", "target": args.target, "validation_features": flags,
                "mte_requested": args.mte, "linear_memory_free": memory_free,
                "ros_operations": sorted(args.ros_operation),
                "assembler_archive_sha256": ARCHIVE_SHA256,
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
    cli.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    cli.add_argument("--ros-operation", action="append", default=[])
    cli.add_argument("--build-receipt", action="store_true")
    cli.add_argument("-g", dest="debug", action="store_true")
    args = cli.parse_args()
    try:
        build(args)
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        cli.exit(1, f"wrwat: {error}\n")


if __name__ == "__main__":
    main()
