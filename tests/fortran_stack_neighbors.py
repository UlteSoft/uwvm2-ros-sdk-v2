"""Check neighboring storage in a real Fortran program on wasm32 and wasm64."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from separate_compilation import Profile, ROOT, candidate_arguments, candidate_command, cgroup_record, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "flang", "runtime", "output"):
        parser.add_argument("--" + key, required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--sysroots", action="append", required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--address-width", type=int, choices=(32, 64),
                        help="check a single address width; defaults to both")
    parser.add_argument("--exception-model", choices=("eh", "noeh"), default="noeh",
                        help="select the supplied sysroot exception ABI")
    parser.add_argument("--storage", choices=("stack", "static-and-heap"), default="stack",
                        help="select local arrays or module variables and allocatable arrays")
    candidate_arguments(parser)
    args = parser.parse_args()
    fixture = Path(__file__).with_name("fortran")
    name = "stack_neighbors" if args.storage == "stack" else "storage_neighbors"
    c_source = fixture / (name + ".c")
    f_source = fixture / (name + ".f90")
    llvm = args.toolchain / "bin"
    inputs = [Path(__file__), c_source, f_source, ROOT / "bin/wrc", ROOT / "bin/wrfortran",
              ROOT / "language/fortran/frontend_fortran.py", llvm / "clang", llvm / "llvm-objdump",
              llvm / "wasm-ld", llvm / "wros-flang-mte", args.flang, args.runtime, *args.sysroots]
    widths = [args.address_width] if args.address_width else [32, 64]
    record = dict(complete=False, cgroup=cgroup_record(), address_widths=widths, storage=args.storage,
                  exception_model=args.exception_model, cases=[], modules={},
                  inputs={str(p): sha(p) for p in inputs})
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(out)

    def save():
        (out / "results.json").write_text(json.dumps(record, indent=2) + "\n")

    def run(name, cmd):
        command = candidate_command(cmd, args.candidate_mte)
        p = subprocess.run(command, cwd=out, capture_output=True, timeout=240)
        (out / (name + ".stdout")).write_bytes(p.stdout)
        (out / (name + ".stderr")).write_bytes(p.stderr)
        record["cases"].append(dict(name=name, command=command, exit=p.returncode))
        save()
        p.check_returncode()
        return p.stdout

    for width in widths:
        flags = ["--target", f"wasm{width}", "--eh" if args.exception_model == "eh" else "--no-eh",
                 "-O3", "-g", "--toolchain", args.toolchain]
        for manifest in args.sysroots:
            flags.extend(["--sysroots", manifest])
        obj = out / f"inspection{width}.o"
        app = out / f"neighbors{width}.wasm"
        run(f"c{width}", [ROOT / "bin/wrc", *flags, "-c", c_source, "-o", obj])
        run(f"fortran{width}", [ROOT / "bin/wrfortran", *flags, "--flang", args.flang,
                                "--link-object", obj, f_source, "-o", app])
        listing = run(f"disassemble{width}", [llvm / "llvm-objdump", "-d", "--mattr=+memtag", app])
        permissions = []
        if args.storage == "stack":
            body = listing.split(b"<capture_fortran>:", 1)[1].split(b"\n\n", 1)[0]
            if body.count(b"memtag.claim") < 2 or body.count(b"memtag.release") < 2:
                raise RuntimeError("Fortran final function lacks two managed stack lifetimes")
        else:
            permissions = ["--wasm-set-main-module-name", "main", "--ros-scene-create", "robot",
                           "--ros-scene-bind", "robot", "main", "--ros-scene-interface", "robot", "abi", "allow"]
            for symbol in (b"_QQmain", b"check_static", b"check_allocatable", b"check_deallocation"):
                if b"<" + symbol + b">:" not in listing:
                    raise RuntimeError("missing a Fortran storage check in the linked module")
        record["modules"][str(width)] = sha(app)
        profile = Profile(width, exceptions=args.exception_model)
        for engine in ("int", "aot"):
            for enabled in (True, False):
                vm_flags = [] if enabled else ["--runtime-disable-memtag"]
                run(f"wasm{width}-{engine}-mte-{enabled}",
                    [args.runtime, *profile.uwvm_feature_flags(), *vm_flags, "--runtime-" + engine,
                     "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                     *permissions, "--run", app])
    if any(sha(Path(p)) != digest for p, digest in record["inputs"].items()):
        raise RuntimeError("qualification inputs changed")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
