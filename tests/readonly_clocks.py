"""Check the SDK clock allowlist, linked Wasm ABI and per-clock VM grants."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import Profile, cgroup_record, inspect, sha, candidate_arguments, candidate_command

GUEST = """
#include <wasi/api.h>
#include <stdint.h>

static void check(__wasi_clockid_t clock, int resolution, int allowed) {
    __wasi_timestamp_t value = UINT64_MAX;
    __wasi_errno_t error = resolution ? __wasi_clock_res_get(clock, &value)
                                      : __wasi_clock_time_get(clock, 1, &value);
    if (allowed) {
        if (error || value == UINT64_MAX || !value) __builtin_trap();
    } else if (error != __WASI_ERRNO_NOTCAPABLE || value != UINT64_MAX) {
        __builtin_trap();
    }
}
void _start(void) {
    check(__WASI_CLOCKID_REALTIME, 0, MASK & 1);
    check(__WASI_CLOCKID_REALTIME, 1, MASK & 2);
    check(__WASI_CLOCKID_MONOTONIC, 0, MASK & 4);
    check(__WASI_CLOCKID_MONOTONIC, 1, MASK & 8);
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    candidate_arguments(parser)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.output.resolve()
    record = dict(cgroup=cgroup_record(), complete=False, cases=[], artifacts={})
    work.mkdir(parents=True, exist_ok=False)
    (work / "tmp").mkdir()
    os.environ["TMPDIR"] = str(work / "tmp")
    source = work / "clock.c"
    source.write_text(GUEST)
    runtime = args.runtime.resolve()
    record["inputs"] = {str(p): sha(p) for p in (runtime, root / "install/frontend.py",
        Path(__file__), args.sysroots, args.toolchain / "bin/clang", args.toolchain / "bin/wasm-ld")}

    def save():
        (work / "results.json").write_text(json.dumps(record, indent=2) + "\n")

    def run(name, argv, expected_error=None):
        command = candidate_command(argv, args.candidate_mte)
        result = subprocess.run(command, cwd=work, capture_output=True, timeout=120)
        (work / (name + ".stderr")).write_bytes(result.stderr)
        record["cases"].append(dict(name=name, command=command, exit=result.returncode))
        save()
        if expected_error is None:
            result.check_returncode()
        elif result.returncode == 0 or expected_error.encode() not in result.stderr:
            raise RuntimeError(name)
        print(name, flush=True)

    for bits in (32, 64):
        suffix = "" if bits == 32 else "_wasm64"
        compiler = [sys.executable, root / "bin/wrc", "--toolchain", args.toolchain.resolve(),
                    "--sysroots", args.sysroots.resolve(), "--target", f"wasm{bits}",
                    "-O3", "-g", "--reactor", "--export", "_start"]
        for mask in (0, 1, 2, 4, 8, 15):
            label = f"clock{bits}-{mask}"
            module = work / (label + ".wasm")
            run(label + "-build", [*compiler, f"-DMASK={mask}", source, "-o", module])
            imports = inspect(module.read_bytes())
            expected = {"clock_time_get" + suffix, "clock_res_get" + suffix}
            if {i["name"] for i in imports} != expected:
                raise RuntimeError("unexpected clock fixture imports")
            record["artifacts"][module.name] = dict(sha256=sha(module), imports=imports)
            policy = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main"]
            for func in sorted(expected):
                policy.extend(("--wasip1-single-interface", "main", func, "allow"))
            for bit, grant in enumerate(("realtime-clock", "realtime-resolution",
                                         "monotonic-clock", "monotonic-resolution")):
                if mask & (1 << bit):
                    policy.extend(("--wasip1-single-grant", "main", grant))
            for engine in ("int", "aot"):
                run(label + "-" + engine, [runtime, *Profile(bits).uwvm_feature_flags(),
                    "--wasm-set-main-module-name", "main", "--runtime-" + engine,
                    "--runtime-llvm-jit-cache-path", "disable", *policy, "--run", module])

        forbidden = work / "forbidden.c"
        for name, statement in (("fd_close", "__wasi_fd_close(0)"),
                                ("sock_shutdown", "__wasi_sock_shutdown(0, 1)")):
            forbidden.write_text("#include <wasi/api.h>\nvoid _start(void){if(" +
                                 statement + ") __builtin_trap();}\n")
            run(f"{name}{bits}-refused", [*compiler, forbidden, "-o", module],
                "unauthorized import or signature")
        for name in ("clock_res_get", "clock_time_get"):
            forbidden.write_text('__attribute__((import_module("wasi_snapshot_preview1"),import_name("' +
                                 name + suffix + '"))) extern int bad(int);\n'
                                 'void _start(void){if(bad(0)) __builtin_trap();}\n')
            run(f"{name}{bits}-bad-signature", [*compiler, forbidden, "-o", module],
                "unauthorized import or signature")
        if sha(module) != record["artifacts"][module.name]["sha256"]:
            raise RuntimeError("a refused link replaced the previous output")
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
