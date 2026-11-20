"""@file vm_guest_profile.py
@brief Run Core 3 modules under the SDK Xmake runner's exact exception policy.
"""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

from separate_compilation import ROOT, cgroup_record, sha

RUNNER = ROOT / "tools/xmake/run_guest.py"

CORE3 = """(module
  (func $check (param i32)
    (if (i32.ne (local.get 0) (i32.const 42)) (then unreachable)))
  (func (export "_start")
    (return_call $check (i32.const 42))))"""

TYPED_EH = """(module
  (tag $value (param i32))
  (func (export "_start")
    (block $caught (result i32)
      (try_table (catch $value $caught)
        (throw $value (i32.const 42)))
      unreachable)
    i32.const 42
    i32.ne
    if unreachable end))"""


def main():
    """@brief Verify that disabling exceptions leaves the other Core 3 features enabled."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", type=Path, required=True)
    parser.add_argument("--wasm-tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    args.output.mkdir(mode=0o700)
    report = {
        "complete": False,
        "cgroup": group,
        "guest_profile_sha256": sha(ROOT / "install/guest_profile.py"),
        "runner_sha256": sha(RUNNER),
        "vm_sha256": sha(args.vm),
        "assembler_sha256": sha(args.wasm_tools),
        "modules": {},
        "cases": [],
    }

    def save():
        (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    env = {"WROS_VM": str(args.vm.resolve(strict=True)), "PATH": os.defpath, "LC_ALL": "C"}

    def run(name, command):
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        log = args.output / (name + ".log")
        log.write_bytes(result.stdout)
        return result, sha(log)

    save()
    for name, source in (("tail-call", CORE3), ("typed-eh", TYPED_EH)):
        text = args.output / (name + ".wat")
        binary = text.with_suffix(".wasm")
        text.write_text(source + "\n")
        assembled, _ = run(name + "-assemble", [args.wasm_tools, "parse", text, "-o", binary])
        if assembled.returncode:
            raise RuntimeError(f"{name} did not assemble")
        report["modules"][name] = sha(binary)

    for engine in ("int", "aot"):
        for name, exceptions, allowed in (("tail-call", "noeh", True), ("typed-eh", "eh", True),
                                          ("typed-eh", "noeh", False)):
            label = f"{engine}-{name}-{exceptions}"
            command = [sys.executable, "-I", "-B", RUNNER, args.output / (name + ".wasm"),
                       "wasm32", "3.0", "single", "--engine", engine, "--exceptions", exceptions, "--check-tags"]
            result, log_digest = run(label, command)
            diagnostic = re.sub(rb"\x1b\[[0-9;]*m", b"", result.stdout)
            correct = (result.returncode == 0 if allowed else
                       result.returncode == 127 and b"requires --wasm-feature-enable-exceptions" in diagnostic)
            report["cases"].append({"case": label, "command": list(map(str, command)),
                                    "allowed": allowed, "exit": result.returncode,
                                    "log_sha256": log_digest})
            save()
            if not correct:
                raise RuntimeError(f"{label} produced an unexpected VM result")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
