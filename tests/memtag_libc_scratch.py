"""Exercise pselect/ppoll cleanup and binary128 formatting in an actual candidate libc."""
import argparse
import json
from pathlib import Path
import resource
import subprocess

from separate_compilation import ROOT, Profile, cgroup_record, inspect, sha
from compiler import compiler_environment, make_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--sysroots", action="append", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--address-bits", type=int, nargs="+", choices=(32, 64), default=(32, 64))
    parser.add_argument("--eh", action="store_true")
    args = parser.parse_args()
    if not args.output.is_relative_to(ROOT / ".tmp"):
        parser.error("choose an unused directory in the SDK .tmp")
    args.output.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    source = ROOT / "tests/memtag/libc_scratch.c"
    files = [source, Path(__file__), args.runtime, *args.sysroots, args.toolchain / "bin/clang",
             args.toolchain / "bin/wasm-ld"]
    report = dict(complete=False, cgroup=cgroup_record(), cases=[], modules={}, inputs={str(p): sha(p) for p in files})
    receipt = args.output / "results.json"

    def save():
        receipt.write_text(json.dumps(report, indent=2) + "\n")

    def run(label, command, env=None):
        cmd = list(map(str, command))
        child = subprocess.run(cmd, capture_output=True, env=env, cwd=args.output, timeout=120)
        (args.output / (label + ".log")).write_bytes(child.stdout + child.stderr)
        report["cases"].append(dict(name=label, argv=cmd, code=child.returncode))
        save()
        child.check_returncode()

    for bits in dict.fromkeys(args.address_bits):
        name = "libc" + str(bits)
        module = args.output / (name + ".wasm")
        profile = Profile(bits, exceptions="eh" if args.eh else "noeh")
        command, _ = make_command(args.toolchain, args.sysroots, profile, "c",
                                  ["-O3", "-g", "-mexec-model=reactor", "-Wl,--export=_start",
                                   "-Wl,--wrap=malloc,--wrap=free,--wrap=__wasi_poll_oneoff", str(source),
                                   "-lc-printscan-long-double", "-o", str(module)], verify=True)
        run(name + "-build", command, {**compiler_environment(args.toolchain), "TMPDIR": str(args.output)})
        imports = inspect(module.read_bytes())
        grants = []
        clock = "clock_time_get" if bits == 32 else "clock_time_get_wasm64"
        for entry in imports:
            if (entry["module"], entry["name"]) != ("wasi_snapshot_preview1", clock) or (
                entry["kind"] != 0 or entry["params"] != ["i32", "i64", f"i{bits}"] or entry["results"] != ["i32"]
            ):
                raise ValueError("unexpected import " + str(entry))
            grants += ["--wasip1-single-create", module.name, "--wasip1-single-enable", module.name,
                       "--wasip1-single-interface", module.name, clock, "deny"]
        report["modules"][name] = dict(sha256=sha(module), imports=imports)
        for engine in ("int", "aot"):
            run(name + "-" + engine, [args.runtime, *profile.uwvm_feature_flags(), "--runtime-" + engine,
                                      "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                                      "--runtime-memtag-mode", "sync", "--runtime-memtag-backend", "software",
                                      *grants, "--run", module])
    report["complete"] = all(sha(Path(p)) == v for p, v in report["inputs"].items())
    save()
    if not report["complete"]:
        raise ValueError("an input changed during the run")


if __name__ == "__main__":
    main()
