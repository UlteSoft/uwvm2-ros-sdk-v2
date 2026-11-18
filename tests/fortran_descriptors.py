"""Build an ordinary Fortran application and run its descriptor semantics in both VM engines."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from separate_compilation import ROOT, Profile, candidate_arguments, candidate_command, cgroup_record, sha
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "runtime", "output"):
        parser.add_argument("--" + key, required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--flang", type=lambda p: Path(p).resolve())
    parser.add_argument("--sysroots", action="append", required=True, type=lambda p: Path(p).resolve())
    parser.add_argument("--address-width", choices=(32, 64), type=int, required=True)
    parser.add_argument("--no-mte", action="store_true")
    candidate_arguments(parser)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(out)
    profile = Profile(args.address_width, mte=not args.no_mte, exceptions="eh")
    sources = Path(__file__).with_name("fortran")
    record = dict(complete=False, cgroup=cgroup_record(), profile=profile.to_dict(), cases=[],
                  inputs={str(path): sha(path) for path in
                          [Path(__file__), sources/"descriptor_status.f90", sources/"descriptor_status.c",
                           ROOT/"language/fortran/frontend_fortran.py", ROOT/"language/fortran/compute_platform.cpp",
                           args.flang or args.toolchain/"bin/flang", args.toolchain/"bin/clang",
                           args.toolchain/"bin/wasm-ld", args.runtime, *args.sysroots]})
    vendor = ROOT / "third-parties/fortran"
    for path in sorted(vendor.rglob("*")):
        if path.is_file():
            record["inputs"][str(path)] = sha(path)
    report = out / "results.json"

    def save():
        report.write_text(json.dumps(record, indent=2) + "\n")

    def run(name, args_list):
        command = candidate_command(args_list, args.candidate_mte)
        result = subprocess.run(command, cwd=out, capture_output=True, timeout=300)
        (out/(name+".stderr")).write_bytes(result.stderr)
        record["cases"].append(dict(name=name, command=command, exit=result.returncode))
        save()
        result.check_returncode()

    flags = ["--toolchain", args.toolchain, "--target", f"wasm{args.address_width}", "--eh", "-O3", "-g"]
    if args.no_mte:
        flags.append("--no-mte")
    for path in args.sysroots:
        flags += ["--sysroots", path]
    obj, app = out/"check.o", out/"descriptor.wasm"
    run("observe", [ROOT/"bin/wrc", *flags, "-I", vendor/"flang/include", "-c", sources/"descriptor_status.c", "-o", obj])
    run("build", [ROOT/"bin/wrfortran", *flags, *(["--flang", args.flang] if args.flang else []),
                  "--link-object", obj, sources/"descriptor_status.f90", "-o", app])
    imports = inspect(app.read_bytes())
    if [(entry["module"], entry["name"]) for entry in imports] != [("uwvm_ros_v2", "abi")]:
        raise RuntimeError("unexpected guest imports: " + repr(imports))
    record["module"] = dict(sha256=sha(app), imports=imports)
    for engine in ("int", "aot"):
        for mode in (("on", "off") if profile.mte else ("off",)):
            run(engine+"-"+mode, [args.runtime, *profile.uwvm_feature_flags(), "--runtime-"+engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                *(["--runtime-disable-memtag"] if mode == "off" else []),
                "--wasm-set-main-module-name", "main", "--ros-scene-create", "robot",
                "--ros-scene-bind", "robot", "main", "--ros-scene-interface", "robot", "abi", "allow",
                "--run", app])
    if any(sha(Path(path)) != digest for path, digest in record["inputs"].items()):
        raise RuntimeError("Fortran qualification input changed")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
