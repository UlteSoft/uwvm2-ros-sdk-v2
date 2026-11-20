"""Compile a standalone Zig controller to audited Core Wasm."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile

from release import (ARCHIVE, PRODUCER, SDK, authorized, digest, local_release,
                     marker_path, producer_archive, profile_for, qualification, receipt)
from artifacts import read_bounded
from compiler import compiler_environment, make_command, select_closure
from frontend import audit
from imports import inspect


def zip_toolchain(toolchain, work):
    """Use a private copy of the exact archive throughout extraction and compilation."""
    archive = work / ARCHIVE
    archive.write_bytes(producer_archive(toolchain))
    with tarfile.open(archive, "r:xz") as packed:
        for entry in packed:
            parts = PurePosixPath(entry.name).parts
            if not parts or parts[0] != PRODUCER or ".." in parts:
                raise ValueError("unexpected Zig archive entry")
            if len(parts) > 1 and parts[1] in {"lib", "zig"}:
                if not entry.isdir() and not entry.isfile():
                    raise ValueError("unexpected Zig archive member type")
                packed.extract(entry, work, filter="data")
    return work / PRODUCER


def build(source, output, toolchain, sysroots, profile, work, marker_digest=None):
    """Lower freshly emitted Zig IR and verify the exact final host imports."""
    if source.suffix != ".zig" or not source.is_file():
        raise ValueError("expected one regular Zig source file")
    app = work / "application.zig"
    app.write_bytes(read_bounded(source))
    (work / "wros_scene.zig").write_bytes(read_bounded(SDK / "language/zig/scene.zig"))
    raw, marked, obj = (work / name for name in ("application.bc", "marked.bc", "application.o"))
    producer = zip_toolchain(toolchain, work)
    env = compiler_environment(toolchain)
    env.update(HOME=str(work), ZIG_GLOBAL_CACHE_DIR=str(work / "global-cache"), ZIG_LOCAL_CACHE_DIR=str(work / "local-cache"),
               TMPDIR=str(work))
    marker = marker_path(toolchain)
    if marker_digest is not None:
        private = work / "marker"
        shutil.copyfile(marker, private)
        if digest(private) != marker_digest:
            raise ValueError("Zig marker changed after release verification")
        private.chmod(0o700)
        marker = private
    bits = profile.address_bits

    def run(argv):
        subprocess.run(argv, cwd=work, env=env, check=True, timeout=120)

    # Preserve Zig's checked semantics while deferring LLVM optimization to
    # the SDK's tagged backend.
    run([producer / "zig", "build-obj", app, "--zig-lib-dir", producer / "lib", "-target",
         f"wasm{bits}-freestanding", "-O", "Debug", "-fllvm", "-fno-emit-bin", "-femit-llvm-bc=" + str(raw),
         "-fno-compiler-rt", "-fno-stack-protector", "-fno-error-tracing"])
    run([marker, str(bits), "on" if profile.mte else "off", raw, marked, source.resolve()])
    command, closure = make_command(toolchain, sysroots, profile, "c",
                                    ["-O3", "-g", "-Wno-override-module", "-c", str(marked), "-o", str(obj)], verify=True)
    run(command)
    # Freestanding wide integer operations may require compiler-rt.
    _, _, _, _, resource = select_closure(sysroots, profile, closure["compiler_sha256"])
    builtin_target = profile.triple.replace("-wasip1", "-unknown-wasip1")
    builtins = resource / "lib" / builtin_target / "libclang_rt.builtins.a"
    command, _ = make_command(toolchain, sysroots, profile, "c",
                              ["-O3", "-g", "-nostdlib", "-Wl,--no-entry,--export=_start,--max-memory=16777216",
                               str(obj), str(builtins), "-o", str(output)])
    run(command)
    data = read_bounded(output)
    audit(data, profile)
    if any(row["module"] != "uwvm_ros_v2" for row in inspect(data)):
        raise ValueError("freestanding Zig only permits the registered ROSv2 imports")
    return digest(app)


def verify(argv):
    p = argparse.ArgumentParser(prog="wrzig verify")
    for name in ("artifact", "receipt", "vm"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--approved-receipt-sha256", required=True)
    args = p.parse_args(argv)
    row, profile, _, _ = authorized(local_release.site_config(SDK))
    data = local_release.read_file(args.receipt, qualification.MAX_RECEIPT_BYTES)
    if hashlib.sha256(data).hexdigest() != args.approved_receipt_sha256:
        raise ValueError("the Zig receipt differs from the operator-approved digest")
    record = json.loads(data, object_pairs_hook=local_release.unique_object)
    if not isinstance(record, dict):
        raise ValueError("invalid Zig receipt")
    source_digest = record.get("source_sha256", "")
    if not isinstance(source_digest, str) or not qualification.HEX.fullmatch(source_digest):
        raise ValueError("missing approved Zig source identity")
    expected = receipt(row, profile, source_digest)
    expected["artifact_sha256"] = digest(args.artifact)
    if expected != record or row["vm_sha256"] != digest(args.vm):
        raise ValueError("Zig artifact, release, compiler profile or VM differs from the approved receipt")
    print(json.dumps(record))


def main():
    try:
        if sys.argv[1:2] == ["verify"]:
            return verify(sys.argv[2:])
        p = argparse.ArgumentParser(prog="wrzig", description=__doc__)
        p.add_argument("source", type=Path)
        p.add_argument("-o", "--output", type=Path, required=True)
        p.add_argument("--target", choices=("wasm32", "wasm64"))
        p.add_argument("--toolchain", type=Path)
        p.add_argument("--sysroots", type=Path, action="append")
        p.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
        p.add_argument("--build-receipt", action="store_true")
        args = p.parse_args()
        bits = int(args.target[4:]) if args.target is not None else None
        if args.output.suffix != ".wasm" or args.source.resolve() == args.output.resolve():
            raise ValueError("expected a separate .wasm output")
        if args.mte:
            if args.toolchain is not None or args.sysroots is not None:
                raise ValueError("tagged Zig build tools come from the signed site profile")
            row, profile, toolchain, sysroots = authorized(local_release.site_config(SDK), bits)
        else:
            if args.toolchain is None or args.sysroots is None:
                raise ValueError("--no-mte requires explicit build tools and an untagged sysroot")
            row = None
            profile, toolchain, sysroots = profile_for(bits or 32, tagged=False), args.toolchain.resolve(), args.sysroots
        with tempfile.TemporaryDirectory(dir=args.output.parent) as scratch:
            work = Path(scratch).resolve()
            staged = work / "application.wasm"
            source_hash = build(args.source, staged, toolchain, sysroots, profile, work,
                                row["inputs"]["marker"] if row is not None else None)
            qualification.finish(receipt(row, profile, source_hash), args, staged, args.output)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.exit("wrzig: " + str(error))
