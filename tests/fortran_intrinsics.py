"""Execute masked sums, dot products, matrix products and reshaping in a real Fortran Wasm guest."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from separate_compilation import Profile, ROOT, candidate_arguments, candidate_command, cgroup_record, inspect, sha
from artifacts import sections
from imports import Reader


def named_functions(data):
    """Read function names from the standardized Wasm name custom section."""
    result = set()
    for _, _, name, section in sections(data):
        if name != "name":
            continue
        while section.position < len(section.data):
            kind = section.byte()
            payload = Reader(section.take(section.uint()))
            if kind == 1:
                for _ in range(payload.count()):
                    payload.uint()
                    result.add(payload.name())
                payload.end()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + key, required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--flang", type=lambda value: Path(value).resolve())
    parser.add_argument("--address-width", type=int, choices=(32, 64), required=True)
    parser.add_argument("--no-mte", action="store_true")
    parser.add_argument("--no-debug", action="store_true", help="exercise the default release without source debug information")
    candidate_arguments(parser)
    args = parser.parse_args()
    profile = Profile(args.address_width, mte=not args.no_mte, exceptions="eh")
    source = ROOT / "tests/fortran/array_intrinsics.f90"
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    environment = {**os.environ, "TMPDIR": str(out)}
    guest = out / "matrix.wasm"
    inputs = [Path(__file__), source, ROOT / "language/fortran/frontend_fortran.py", args.runtime,
              args.flang or args.toolchain / "bin/flang", args.toolchain / "bin/clang",
              args.toolchain / "bin/wasm-ld", args.sysroots]
    record = dict(complete=False, debug=not args.no_debug, cgroup=cgroup_record(), profile=profile.to_dict(), cases=[],
                  inputs={str(path): sha(path) for path in inputs})
    receipt = out / "results.json"

    def save():
        receipt.write_text(json.dumps(record, indent=2) + "\n")

    def run(name, argv):
        command = candidate_command(argv, args.candidate_mte)
        with (out / (name + ".log")).open("wb") as log:
            child = subprocess.run(command, cwd=out, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=420)
        record["cases"].append(dict(name=name, command=command, exit=child.returncode))
        save()
        child.check_returncode()

    run("compile", [ROOT / "bin/wrf", "--toolchain", args.toolchain, "--sysroots", args.sysroots,
                    "--target", "wasm" + str(args.address_width), "--eh", "-O3", *([] if args.no_debug else ["-g"]),
                    *(["--no-mte"] if args.no_mte else []), *(["--flang", args.flang] if args.flang else []),
                    source, "-o", guest])
    data = guest.read_bytes()
    requirements = {"_FortranA" + operation for operation in ("Any", "Reshape", "SumDim", "SumReal8",
                    "DotProductReal8", "MatmulReal8Real8", "DotProductInteger4", "MatmulInteger4Integer4",
                    "MatmulLogical4Logical4")}
    missing = requirements - named_functions(data)
    if missing:
        raise ValueError("missing upstream Flang procedures: " + ", ".join(sorted(missing)))
    imports = inspect(data)
    if [(row["module"], row["name"]) for row in imports] != [("uwvm_ros_v2", "abi")]:
        raise ValueError("unexpected host imports")
    record["guest"] = dict(sha256=sha(guest), imports=imports, runtime_procedures=sorted(requirements))
    for engine in ("int", "aot"):
        for enabled in ((True, False) if profile.mte else (False,)):
            run(engine + ("-on" if enabled else "-off"), [args.runtime, *profile.uwvm_feature_flags(),
                "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                *([] if enabled else ["--runtime-disable-memtag"]), "--wasm-set-main-module-name", "main",
                "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main", "--ros-scene-interface",
                "robot", "abi", "allow", "--run", guest])
    if any(sha(Path(path)) != digest for path, digest in record["inputs"].items()):
        raise ValueError("Fortran qualification inputs changed")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
