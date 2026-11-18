"""Check Fortran SYSTEM_CLOCK and CPU_TIME in real guests with independent VM clock grants."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from separate_compilation import Profile, ROOT, candidate_arguments, candidate_command, cgroup_record, inspect, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--sdk", default=ROOT, type=lambda path: Path(path).resolve(),
                        help="installed Fortran SDK or source checkout")
    parser.add_argument("--flang", type=lambda path: Path(path).resolve())
    parser.add_argument("--address-width", required=True, type=int, choices=(32, 64))
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--no-mte", action="store_true")
    candidate_arguments(parser)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    bits = args.address_width
    profile = Profile(bits, exceptions="eh", mte=not args.no_mte)
    inputs = [Path(__file__), ROOT / "tests/fortran/clocks.f90", args.sdk / "language/fortran/clock.c",
              args.sdk / "language/fortran/frontend_fortran.py", args.toolchain / "bin/clang",
              args.toolchain / "bin/wasm-ld", args.flang or args.toolchain / "bin/flang", args.sysroots, args.runtime]
    report = dict(complete=False, cgroup=cgroup_record(), profile=profile.to_dict(), debug=not args.no_debug,
                  inputs={str(path): sha(path) for path in inputs}, cases=[], guests={})
    env = {**os.environ, "TMPDIR": str(out), "PYTHONDONTWRITEBYTECODE": "1"}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, expected_error=None):
        cmd = candidate_command(argv, args.candidate_mte)
        with (out / (name + ".log")).open("wb") as stream:
            proc = subprocess.run(cmd, cwd=out, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=420)
        report["cases"].append(dict(name=name, exit=proc.returncode, command=cmd,
                                    expected_success=expected_error is None, expected_error=expected_error))
        save()
        if expected_error is None:
            proc.check_returncode()
        elif proc.returncode == 0 or expected_error not in (out / (name + ".log")).read_text(errors="replace"):
            raise RuntimeError("unexpected result for " + name)

    flags = [args.sdk / "bin/wrf", "--toolchain", args.toolchain, "--sysroots", args.sysroots, "--target", f"wasm{bits}",
             "--eh", "-O3", *([] if args.no_debug else ["-g"]), *(["--no-mte"] if args.no_mte else []),
             *(["--flang", args.flang] if args.flang else [])]
    for monotonic, process in ((False, False), (True, False), (False, True), (True, True)):
        label = f"monotonic-{int(monotonic)}-process-{int(process)}"
        settings = out / (label + ".f90")
        settings.write_text("module expected_clocks\n  logical, parameter :: "
                            f"elapsed=.{str(monotonic).lower()}., cpu=.{str(process).lower()}.\nend module\n")
        app = out / (label + ".wasm")
        run("build-" + label, [*flags, settings, ROOT / "tests/fortran/clocks.f90", "-o", app])
        imports = inspect(app.read_bytes())
        expected_name = "clock_time_get_wasm64" if bits == 64 else "clock_time_get"
        if [(imp["module"], imp["name"]) for imp in imports] != [("wasi_snapshot_preview1", expected_name)]:
            raise RuntimeError("unexpected Fortran clock imports")
        report["guests"][label] = dict(sha256=sha(app), imports=imports)
        if bits == 64 and not monotonic and not process:
            run("reject-wasm32-interface-only", [args.runtime, *profile.uwvm_feature_flags(), "--runtime-int",
                "--wasm-set-main-module-name", "main", "--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                "--wasip1-single-interface", "main", "clock_time_get", "allow", "--run", app],
                "the interface exposure permission is hidden")
        for engine in ("int", "aot"):
            run(label + "-" + engine, [args.runtime, *profile.uwvm_feature_flags(), "--runtime-" + engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                "--wasm-set-main-module-name", "main", "--wasip1-single-create", "main",
                "--wasip1-single-enable", "main", "--wasip1-single-interface", "main", expected_name, "allow",
                *(["--wasip1-single-grant", "main", "monotonic-clock"] if monotonic else []),
                *(["--wasip1-single-grant", "main", "process-clock"] if process else []), "--run", app])
    # An archive can reference a clock from an object its consumer never uses.
    # The linker must not introduce WASI into that consumer.
    unused = out / "unused_clock.f90"
    unused.write_text("integer(8) function elapsed_ticks() bind(c)\n  call system_clock(elapsed_ticks)\nend function\n")
    archive = out / "optional.a"
    run("archive-optional-clock", [*flags, "--static", unused, "-o", archive])
    body = out / "standalone.f90"
    body.write_text("program standalone\nend program\n")
    standalone = out / "standalone.wasm"
    run("link-unused-clock", [*flags, "--link-object", archive, body, "-o", standalone])
    if inspect(standalone.read_bytes()):
        raise RuntimeError("an unreferenced library member introduced a host import")
    run("run-without-host-imports", [args.runtime, *profile.uwvm_feature_flags(), "--runtime-int", "--run", standalone])
    if any(sha(Path(path)) != digest for path, digest in report["inputs"].items()):
        raise RuntimeError("Fortran clock inputs changed")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
