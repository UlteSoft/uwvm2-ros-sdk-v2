"""Exercise the complete TinyGo producer and both VM engines in the 64 GiB cgroup."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys

from separate_compilation import Profile, cgroup_record, inspect, sha, candidate_arguments, candidate_command

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("goroot", "tinygoroot", "toolchain", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=lambda name: Path(name).resolve())
    parser.add_argument("--sysroots", type=lambda name: Path(name).resolve(), required=True, action="append")
    parser.add_argument("--sdk", type=Path, default=ROOT, help="SDK tree or selective development installation")
    parser.add_argument("--host-cxx", type=Path)
    candidate_arguments(parser)
    args = parser.parse_args()
    work, sdk = args.output, args.sdk.resolve()
    record = dict(complete=False, cgroup=cgroup_record(), cases=[], artifacts={}, vm_sha256=sha(args.runtime))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    work.mkdir(parents=True, exist_ok=False)
    app = work / "app"
    app.mkdir()
    (app / "go.mod").write_text("module example.local/wros-test\n\ngo 1.24\n\nrequire wros.local/scene v0.0.0\n"
                               "replace wros.local/scene => " + json.dumps(str(sdk / "language/tinygo/scene")) + "\n")
    source = app / "main.go"
    wasm = work / "body.wasm"
    def save():
        (work / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    def run(label, command, expect=None):
        argv = candidate_command(command, args.candidate_mte)
        result = subprocess.run(argv, cwd=work, capture_output=True, timeout=240)
        (work / (label + ".stderr")).write_bytes(result.stderr)
        record["cases"].append(dict(name=label, argv=argv, exit=result.returncode))
        save()
        valid = result.returncode == 0 if expect is None else result.returncode != 0 and expect.encode() in result.stderr
        if not valid:
            raise RuntimeError(f"{label} returned {result.returncode}: {result.stderr[-1200:]!r}")
        return result.stdout

    compiler = [sys.executable, sdk / "bin/wrtg", app, "--goroot", args.goroot, "--tinygoroot",
                args.tinygoroot, "--toolchain", args.toolchain, "--print-identity",
                "-o", wasm]
    for receipt in args.sysroots:
        compiler += ["--sysroots", receipt]
    if args.host_cxx:
        compiler += ["--host-cxx", args.host_cxx]
    base = [args.runtime, *Profile().uwvm_feature_flags(), "--runtime-memtag-mode", "sync",
            "--runtime-memtag-backend", "software", "--runtime-memtag-action", "crash",
            "--wasm-set-main-module-name", "main", "--runtime-llvm-jit-cache-path", "disable",
            "--ros-scene-create", "compute", "--ros-scene-bind", "compute", "main"]
    grant = ["--ros-scene-interface", "compute", "abi", "allow"]
    (app / "mode_on.go").write_text("//go:build wros_mte\n\npackage main\nconst tagged=true\n")
    (app / "mode_off.go").write_text("//go:build wros_nomte\n\npackage main\nconst tagged=false\n")
    cases = [("collector-eh", []), ("collector-noeh", ["--no-eh"]),
             ("nomte-eh", ["--no-mte"]), ("nomte-noeh", ["--no-mte", "--no-eh"])]
    source.write_bytes((ROOT / "tests/tinygo/collector.go").read_bytes())
    for label, flags in cases:
        identity = json.loads(run(label + "-build", [*compiler, *flags]))
        suppressions = identity["source_suppressions"]
        if "main.rawStack" not in suppressions["functions"] or "main.rawData" not in suppressions["globals"]:
            raise RuntimeError(f"source suppression did not reach producer IR: {suppressions}")
        imports = inspect(wasm.read_bytes())
        if [(x["module"], x["name"]) for x in imports] != [("uwvm_ros_v2", "abi")] or identity["sha256"]["guest"] != sha(wasm):
            raise RuntimeError("unexpected final import surface or producer identity")
        record["artifacts"][label] = dict(imports=imports, identity=identity)
        retained = work / (label + ".wasm")
        retained.write_bytes(wasm.read_bytes())
        for engine in ("int", "aot"):
            launch = [*base, "--runtime-" + engine]
            run(label + "-" + engine, [*launch, *grant, "--run", retained])
            run(label + "-" + engine + "-refused", [*launch, "--ros-scene-interface", "compute", "abi", "deny",
                                                  "--run", retained], "catch unreachable")
            run(label + "-" + engine + "-extension-disabled", [*launch, "--wasm-feature-disable-memtag-extension",
                *grant, "--run", retained], "requires memtag-extension" if "--no-mte" not in flags else None)

    source.write_text('package main\nimport "time"\nfunc main(){ if time.Now().Unix() <= 0 { panic("invalid clock") } }\n')
    clock_identity = json.loads(run("clock-build", compiler))
    clock_imports = inspect(wasm.read_bytes())
    if [(row["module"], row["name"]) for row in clock_imports] != [("wasi_snapshot_preview1", "clock_time_get")]:
        raise RuntimeError("unexpected time.Now import surface")
    record["artifacts"]["clock"] = dict(identity=clock_identity, imports=clock_imports)
    clocks = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
              "--wasip1-single-interface", "main", "clock_time_get", "allow"]
    for engine in ("int", "aot"):
        launch = [*base, "--runtime-" + engine, *clocks, "--wasip1-single-grant", "main", "monotonic-clock"]
        run("clock-allow-" + engine, [*launch, "--wasip1-single-grant", "main", "realtime-clock", "--run", wasm])
        run("clock-deny-realtime-" + engine, [*launch, "--run", wasm], "catch unreachable")
    previous = sha(wasm)
    for name, flags, error in [("memory64", ["--target", "wasm64"], "invalid choice"),
                               ("threads", ["--threads"], "unrecognized arguments")]:
        run("reject-" + name, [*compiler, *flags], error)
    source.write_text('package main\n//go:wasmimport wasi_snapshot_preview1 fd_close\n'
                      'func closefd(uint32) uint32\nfunc main(){if closefd(7)!=0 {panic("denied")}}\n')
    run("reject-broad-wasi", compiler, "unauthorized import or signature")
    if sha(wasm) != previous:
        raise RuntimeError("a rejected build changed the published guest")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
