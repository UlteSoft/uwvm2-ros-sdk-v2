"""@file managed_binding_controls.py
@brief Verify typed Mono binding admission and an authorized handshake without a device.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from platform_examples import ROOT, sha
sys.path.insert(0, str(ROOT / "tools/xmake"))
from guest_profile import Profile
from platform_driver_test import run_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(exist_ok=False)
    route = next(row[3:] for row in Path("/proc/self/cgroup").read_text().splitlines() if row.startswith("0::"))
    group = Path("/sys/fs/cgroup") / route.lstrip("/")
    if tuple((group / item).read_text().strip() for item in ("memory.max", "memory.swap.max")) != (str(64 << 30), "0"):
        parser.error("use an existing 64 GiB cgroup with swap disabled")
    vm = args.vm.resolve(strict=True)
    options = [ROOT / "bin/wrfs", "--dotnet", os.environ["WROS_DOTNET"], "--mono-compiler", os.environ["WROS_MONO"],
               "--toolchain", os.environ["WROS_TOOLCHAIN"], "--driver-entry", "Driver.Start"]
    original = (ROOT / "examples/shared/extension/fsharp/Driver.fs").read_text()
    source = args.output / "Driver.fs"
    wasm = args.output / "Driver.wasm"
    report = {"complete": False, "vm": sha(vm), "cgroup": route, "positive": {}, "rejected": {}}
    try:
        source.write_text(original.replace("status = 13", "status = 11"))
        subprocess.run([*options, source, "-o", wasm], check=True, timeout=120)
        expected = sha(wasm)
        for engine in ("int", "aot"):
            argv = [str(vm), *Profile(mte=True).uwvm_feature_flags(), "--wasm-set-main-module-name", "main",
                    "--runtime-" + engine, "--runtime-compile-threads", "3", "--runtime-llvm-jit-cache-path", "disable",
                    "--debug-fault-action", "exit", "--runtime-memtag-mode", "sync"]
            if engine == "aot":
                argv.extend(["--runtime-llvm-jit-full-policy", "legacy-light"])
            status, lengths = run_case(argv, wasm, "unitree", parent_allowed=True, child_allowed=True)
            if status or not lengths:
                raise ValueError(f"{engine}: missing authorized handshake, status {status}, packets {lengths}")
            report["positive"][engine] = lengths
        for case, expression in (("other_method", "Wros.Scene.Abi()"),
                                 ("invalid_alias", 'Wros.Scene.DriverConnectionStatus("../arm")'),
                                 ("long_alias", 'Wros.Scene.DriverConnectionStatus("' + "a" * 64 + '")')):
            source.write_text(original.replace('Wros.Scene.DriverConnectionStatus("arm")', expression))
            result = subprocess.run([*options, source, "-o", wasm], capture_output=True, timeout=120)
            if not result.returncode or b"scene entry must return" not in result.stderr or sha(wasm) != expected:
                raise ValueError(case + " did not reject the changed input while preserving the previous output")
            report["rejected"][case] = result.stderr.decode().strip()
        report["complete"] = True
    finally:
        (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
