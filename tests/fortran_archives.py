"""Compile a Fortran library, link its sealed members and run the resulting Wasm application."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from separate_compilation import Profile, ROOT, candidate_arguments, candidate_command, cgroup_record, inspect, sha
from artifacts import archive_members, check_object, read_bounded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--sdk", default=ROOT, type=lambda path: Path(path).resolve(),
                        help="SDK source tree or installed site with reviewed language releases")
    parser.add_argument("--dlapy3", type=lambda path: Path(path).resolve(),
                        help="unmodified Lite3 LAPACK dlapy3.f from the qualified vendor snapshot")
    parser.add_argument("--dladiv", type=lambda path: Path(path).resolve(),
                        help="unmodified ROS Taskflow LAPACK dladiv.f from the qualified release")
    parser.add_argument("--flang", type=lambda path: Path(path).resolve())
    parser.add_argument("--address-width", type=int, choices=(32, 64), required=True)
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--no-mte", action="store_true")
    candidate_arguments(parser)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    profile = Profile(args.address_width, mte=not args.no_mte, exceptions="eh")
    example = args.sdk / "examples/fortran/static"
    kernels = [example / "kernel.f90"]
    source = example / "body.f90"
    if args.dlapy3 or args.dladiv:
        if not args.dlapy3 or not args.dladiv:
            parser.error("supply both original LAPACK source files")
        expected = [(args.dlapy3, "2d18f7a22e06f99c884a5aeca130883fd1b9f8b82e76c1bc2f1eb66566eed5c8"),
                    (args.dladiv, "8c9c60ccd851af18be83a44b1acd8bfb75a0cf8e90b8bf1b8d7b257b1cc11d22")]
        if any(sha(path) != digest for path, digest in expected):
            raise ValueError("operator-supplied LAPACK source differs from the checked corpus revision")
        kernels = [args.dlapy3, args.dladiv]
        source = ROOT / "tests/fortran/lapack_application.f90"
    library = out / "filter.a"
    app = out / "robot.wasm"
    env = {**os.environ, "TMPDIR": str(out), "PYTHONDONTWRITEBYTECODE": "1"}
    inputs = [Path(__file__), source, *kernels,
              args.sdk / "language/fortran/frontend_fortran.py", args.runtime, args.toolchain / "bin/clang",
              args.toolchain / "bin/wasm-ld", args.flang or args.toolchain / "bin/flang", args.sysroots]
    report = dict(complete=False, cgroup=cgroup_record(), profile=profile.to_dict(),
                  debug=not args.no_debug, cases=[], inputs={str(path): sha(path) for path in inputs})

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(label, arguments, success=True):
        argv = candidate_command(arguments, args.candidate_mte)
        with (out / (label + ".log")).open("wb") as stream:
            proc = subprocess.run(argv, cwd=out, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=420)
        report["cases"].append(dict(name=label, command=argv, exit=proc.returncode, expected_success=success))
        save()
        if (proc.returncode == 0) != success:
            raise RuntimeError("unexpected " + label + " result; check its log")

    flags = [args.sdk / "bin/wrf", "--toolchain", args.toolchain, "--sysroots", args.sysroots, "--eh",
             "--target", "wasm" + str(args.address_width), "-O3", *([] if args.no_debug else ["-g"]),
             *(["--no-mte"] if args.no_mte else []), *(["--flang", args.flang] if args.flang else [])]
    run("archive", [*flags, "--static", *kernels, "-o", library])
    members = archive_members(read_bounded(library))
    if len(members) != len(kernels):
        raise ValueError("archive member count differs from the number of translation units")
    for member in members:
        check_object(member, profile.to_dict(), report["inputs"][str(args.toolchain / "bin/clang")])
    report["archive_sha256"] = sha(library)
    run("reject-nested-archives", [*flags, "--static", "--link-object", library, *kernels,
                                  "-o", library], success=False)
    if sha(library) != report["archive_sha256"]:
        raise RuntimeError("rejected command changed the existing library")
    run("link", [*flags, "--link-object", library, source, "-o", app])
    imports = inspect(read_bounded(app))
    if [(i["module"], i["name"]) for i in imports] != [("uwvm_ros_v2", "abi")]:
        raise RuntimeError("unexpected final host interface")
    report["guest"] = dict(sha256=sha(app), imports=imports)
    for engine in ("int", "aot"):
        for checked in ((True, False) if profile.mte else (False,)):
            run(engine + ("-on" if checked else "-off"), [args.runtime, *profile.uwvm_feature_flags(),
                "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                *([] if checked else ["--runtime-disable-memtag"]), "--wasm-set-main-module-name", "main",
                "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main", "--ros-scene-interface",
                "robot", "abi", "allow", "--run", app])
    if any(sha(Path(path)) != digest for path, digest in report["inputs"].items()):
        raise RuntimeError("Fortran archive inputs changed")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
