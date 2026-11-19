"""@brief Build a scalar Go controller with the fixed Wasm-only Go compiler."""
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
from registers import module

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "language/go"
LIMIT = 1 << 20


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(source, output, *, tagged=True, ros_abi=False, receipt=False):
    """@brief Compile one Go source with the digest-bound host compiler.
    @param source File containing at most 1 MiB of Go source.
    @param output Local path for the validated core Wasm module.
    @param tagged Whether the application requested MTE. All published Go scalar
    guests statically exclude memory and therefore require no tag instructions.
    @param ros_abi Whether to pass the authorized ROSv2 ABI to Start.
    @param receipt Publish a source, compiler and guest digest sidecar.
    """
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("the published Go host compiler requires Linux x86-64")
    if source.suffix != ".go" or output.suffix != ".wasm" or source.resolve() == output.resolve():
        raise ValueError("choose one .go input and a distinct .wasm output")
    with source.open("rb") as stream:
        body = stream.read(LIMIT + 1)
    if not 1 <= len(body) <= LIMIT:
        raise ValueError("expected a Go source file of at most 1 MiB")
    lock = json.loads((LANGUAGE / "release.json").read_bytes())
    item = LANGUAGE / "linux-amd64/producer.xz"
    if item.stat().st_size != lock["compressed_bytes"] or not 0 < lock["binary_bytes"] <= 32 << 20:
        raise ValueError("unexpected Go compiler package size")
    payload = item.read_bytes()
    if sha(payload) != lock["compressed_sha256"]:
        raise ValueError("Go compiler package differs from the reviewed release")
    with tempfile.TemporaryDirectory(dir=output.absolute().parent) as tmp:
        stage = Path(tmp)
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128 << 20)
        executable = decoder.decompress(payload, max_length=lock["binary_bytes"] + 1)
        if (not decoder.eof or decoder.unused_data or len(executable) != lock["binary_bytes"]
                or sha(executable) != lock["binary_sha256"]):
            raise ValueError("Go compiler differs from its reviewed release")
        tool = stage / "wrgo-producer"
        tool.write_bytes(executable)
        tool.chmod(0o700)
        (stage / "input.go").write_bytes(body)
        subprocess.run([tool.resolve()], cwd=stage, env={"GOOS": "wasip1", "GOARCH": "wasm", "LC_ALL": "C", "PATH": "/nonexistent"},
                       timeout=90, check=True)
        with (stage / "compiler.jsonl").open("rb") as stream:
            ir = stream.read((8 << 20) + 1)
        if len(ir) > 8 << 20:
            raise ValueError("Go proof exceeds 8 MiB")
        graph = [json.loads(line) for line in ir.splitlines()]
        artifact = module(graph, ros_abi)
        target = stage / "result.wasm"
        target.write_bytes(artifact)
        sidecar = Path(str(output) + ".wros-go.json")
        record = dict(format="wros-go-register-proof", language="go", profile="register-only",
                      address_bits=32, mte_requested=tagged, linear_memories=0, source_sha256=sha(body),
                      compiler_sha256=lock["binary_sha256"], wasm_sha256=sha(artifact),
                      wasm_imports=["uwvm_ros_v2.abi"] if ros_abi else [],
                      exports=sorted(f["name"] for f in graph) + ["_start"])
        if receipt:
            proof = stage / "build.json"
            proof.write_text(json.dumps(record, indent=2) + "\n")
            os.replace(proof, sidecar)
        else:
            sidecar.unlink(missing_ok=True)
        os.replace(target, output)


def main():
    """@brief Parse Wasm guest options and report build errors on stderr."""
    parser = argparse.ArgumentParser(prog="wrgo", description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--target", choices=("wasm32",), default="wasm32")
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ros-abi", action="store_true", help="pass the authorized ROSv2 ABI number to Start")
    parser.add_argument("--build-receipt", action="store_true")
    args = parser.parse_args()
    try:
        build(args.source, args.output, tagged=args.mte, ros_abi=args.ros_abi, receipt=args.build_receipt)
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError, subprocess.SubprocessError) as e:
        parser.exit(1, "wrgo: " + str(e) + "\n")
