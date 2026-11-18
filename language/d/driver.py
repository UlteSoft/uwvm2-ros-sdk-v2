"""Lower BetterC source to LLVM IR and build it with the reviewed WasmMTE backend."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from release import BUILD, ENV, LOADER, PROFILE, SDK, SETTINGS, authorized, canon, digest, local_release
from compiler import compiler_environment, make_command
from frontend import audit
from artifacts import read_bounded, strip_notes
import qualification


def build(source, output, tc, manifests, work, evidence=None):
    if source.suffix != ".d" or source.resolve() == output.resolve():
        raise ValueError("expected one D source and a separate Wasm output")
    app = work / "application.d"
    app.write_bytes(read_bounded(source))
    ir, marked, obj = (work / name for name in ("application.ll", "marked.bc", "application.o"))
    bindings = SDK / "language/d"
    ldc = (tc / "bin/wros-ldc2").resolve(strict=True)
    cfg = bindings / "frontend.conf"
    subprocess.run([LOADER, ldc, "-conf=" + str(cfg), "-mtriple=wasm32-unknown-wasip1", "-betterC", "-O0", "-g",
                    "-c", "-output-ll", "-I=" + str(tc / "share/wros/betterc/imports"), "-I=" + str(bindings),
                    "-of=" + str(ir), app], cwd=work, env=ENV, check=True)
    env = compiler_environment(tc)
    subprocess.run([tc / "bin/wros-flang-mte", "32", "on", ir, marked], cwd=work, env=env, check=True)
    for flags in (["-O3", "-g", "-x", "ir", "-c", str(marked), "-o", str(obj)],
                  ["-O3", "-g", "-ffunction-sections", "-I" + str(SDK / "include"), "-nostartfiles", "-Wl,--no-entry",
                   "-Wl,--export=_start", str(bindings / "entry.c"), str(bindings / "imports.c"), str(obj), "-o", str(output)]):
        command, _ = make_command(tc, manifests, PROFILE, "c", flags, verify=True)
        subprocess.run(command, cwd=work, env=env, check=True)
    data = strip_notes(read_bounded(output))
    audit(data, PROFILE)
    output.write_bytes(data)
    if evidence is not None:
        evidence.update(frontend=digest(ir), instrument=digest(marked), compile=digest(obj), link=digest(output))
    return digest(app)


def verify(args):
    p = argparse.ArgumentParser(prog="wrd verify")
    for key in ("artifact", "receipt", "vm"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--approved-receipt-sha256", required=True)
    o = p.parse_args(args)
    row = authorized(local_release.site_config(SDK))
    data = local_release.read_file(o.receipt, qualification.MAX_RECEIPT_BYTES)
    if hashlib.sha256(data).hexdigest() != o.approved_receipt_sha256:
        raise ValueError("the BetterC build receipt differs from the approved digest")
    record = json.loads(data, object_pairs_hook=local_release.unique_object)
    if not isinstance(record.get("source_sha256"), str) or not qualification.HEX.fullmatch(record["source_sha256"]):
        raise ValueError("missing D source digest in the approved receipt")
    expected = receipt(row, record["source_sha256"])
    expected["artifact_sha256"] = digest(o.artifact)
    if expected != record or row["vm_sha256"] != digest(o.vm):
        raise ValueError("BetterC artifact, VM or signed release identity differs")
    print(json.dumps(record))


def receipt(row, source_sha256):
    return {"format": BUILD, "source_sha256": source_sha256, "language": "d", "mode": "strict", "profile": PROFILE.to_dict(), "settings": SETTINGS,
            "release_sha256": canon(row), "c_release_sha256": row["c_release_sha256"], "vm_sha256": row["vm_sha256"]}


def main():
    try:
        if sys.argv[1:2] == ["verify"]:
            return verify(sys.argv[2:])
        p = argparse.ArgumentParser(prog="wrd", description=__doc__)
        p.add_argument("source", type=Path)
        p.add_argument("-o", "--output", required=True, type=Path)
        p.add_argument("--target", choices=("wasm32",), default="wasm32")
        p.add_argument("-O", choices=("3",), default="3")
        p.add_argument("-g", action="store_true", default=True)
        p.add_argument("--build-receipt", action="store_true")
        opts = p.parse_args()
        site = local_release.site_config(SDK)
        row = authorized(site)
        with tempfile.TemporaryDirectory(dir=opts.output.parent) as tmp:
            work = Path(tmp).resolve()
            wasm = work / "controller.wasm"
            if opts.source.resolve() == opts.output.resolve():
                raise ValueError("output aliases D source")
            source_hash = build(opts.source, wasm, Path(site["toolchain"]), list(map(Path, site["sysroots"])), work)
            qualification.finish(receipt(row, source_hash), opts, wasm, opts.output)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.exit("wrd: " + str(error))
