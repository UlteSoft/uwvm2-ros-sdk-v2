"""Exercise the public C driver and xmake runner with real core and forbidden ABI inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--candidate-mte", action="store_true", help="test the explicitly unqualified tagged build profile")
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    executable = ROOT / "bin/wrc"
    environment = {**os.environ, "TMPDIR": str(out), "WROS_VM": str(args.runtime.resolve()), "WROS_RUN_QUERIES": "abi"}
    result = {"complete": False, "cgroup": cgroup_record(), "cases": []}

    def run(label, command, expected_error=None):
        child = subprocess.run(command, capture_output=True, env=environment, timeout=120)
        (out / (label + ".stderr")).write_bytes(child.stderr)
        ok = child.returncode == 0 if expected_error is None else child.returncode != 0 and expected_error in child.stderr
        result["cases"].append({"name": label, "passed": ok, "code": child.returncode, "argv": list(map(str, command))})
        (out / "results.json").write_text(json.dumps(result, indent=2))
        if not ok:
            raise RuntimeError(label + ": " + child.stderr.decode(errors="replace")[-1000:])

    flags = [sys.executable, executable, "--toolchain", args.toolchain.resolve(), "--sysroots", args.sysroots.resolve(), "-O3", "-g"]
    if args.candidate_mte:
        flags.append("--legacy-mte")
    body = out / "app.c"
    target = out / "app.wasm"
    body.write_text('#include <wros/scene.h>\nvoid _start(void) {if (wr_abi()!=2) __builtin_trap();}\n')
    link = ["--reactor", "--export", "_start"]
    run("core", [*flags, *link, body, "-o", target])
    good = target.read_bytes()
    run("xmake-core", [sys.executable, ROOT / "tools/xmake/run_guest.py", target, "wasm32", "3.0", "single"])
    for version in ("2", "3"):
        ns = "wasi:cli/environment@0." + version + ".0"
        body.write_text(f'__attribute__((import_module("{ns}"),import_name("get-environment")))\n'
                        'unsigned forbidden(void);\nvoid _start(void){ if (forbidden()) __builtin_trap(); }\n')
        for stage, options, suffix in (("link", link, ".wasm"), ("object", ["-c"], ".o")):
            dest = target.with_suffix(suffix)
            before = dest.read_bytes() if dest.exists() else None
            run("preview" + version + "-" + stage, [*flags, *options, body, "-o", dest], b"prohibited")
            assert (dest.read_bytes() if dest.exists() else None) == before
        run("preview" + version + "-target", [*flags, "--target", "wasm32-wasip" + version, body, "-o", target], b"invalid choice")
    assert target.read_bytes() == good
    result["artifact_sha256"] = hashlib.sha256(good).hexdigest()
    result["complete"] = True
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
