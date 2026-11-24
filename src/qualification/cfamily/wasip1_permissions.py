"""Replay public library guests while granting WASIp1 stdout access one step at a time."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sysroot_suite import add_vm_identity_options, digest, verified_vm

CASES = {
    "upstream/lz4/examples/simple_buffer.c": "c",
    "upstream/fast_float/tests/wide_char_test.cpp": "cpp",
    "gcc-object": "objc",
    "chromium-swizzler": "objcpp",
}
STAGES = ("hidden", "deny", "allow-without-grant", "stdout-only")
ANSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")


def policy(command, guest, owner, vm, interface, stage):
    """Preserve the baseline's other import states and remove both stream grants."""
    result = [str(vm)]
    i = 1
    found = False
    while i < len(command):
        token = command[i]
        if token == "--wasip1-single-grant" and command[i + 2] in ("stdout.write", "stderr.write"):
            i += 3
        elif token == "--wasip1-single-interface" and command[i + 2] == interface:
            found = True
            if stage != "hidden":
                result.extend([token, command[i + 1], interface, "deny" if stage == "deny" else "allow"])
            i += 4
        elif token == "--wasm-preload-library":
            if owner is None:
                raise ValueError("shared-memory owner missing")
            result.extend([token, str(owner), command[i + 2]])
            i += 3
        elif token == "--run" and i == len(command) - 2:
            if stage == "stdout-only":
                result.extend(["--wasip1-single-grant", "main", "stdout.write"])
            result.extend([token, str(guest)])
            break
        else:
            result.append(token)
            i += 1
    if not found or result[-1] != str(guest):
        raise ValueError("unrecognized library invocation")
    return result


def select_rows(directory, objc, vm):
    for line in (directory / "results.jsonl").read_text().splitlines():
        row = json.loads(line)
        case = row["case" if objc else "source"]
        if case not in CASES:
            continue
        language = CASES[case]
        path = Path(case)
        rel = Path(row["profile"]) / case if objc else Path(row["profile"]) / row["family"] / path.parent.name / path.name
        base = directory / rel
        guest = base / "guest.wasm"
        owner = base / "owner.wasm" if "-threads-" in row["profile"] else None
        if any(row["vm"][k] != vm[k] for k in ("commit", "tree", "sha256")):
            raise ValueError(f"{case} uses a different VM")
        if row["status"] != ("executed" if objc else "linked") or digest(guest) != row["wasm_sha256"]:
            raise ValueError(f"missing linked input or guest digest mismatch: {guest}")
        if owner and digest(owner) != (row["memory_owner_sha256"] if objc else row["memory_owner"]["sha256"]):
            raise ValueError(f"memory owner digest mismatch: {owner}")
        interface, = [v["name"] for v in row["imports"] if v["module"] == "wasi_snapshot_preview1"
                      and v["name"] in ("fd_write", "fd_write_wasm64")]
        for engine in ("int", "aot"):
            run = row["stages" if objc else "runs"][engine]
            expected = (base / (engine + ".out")).read_bytes()
            if not expected or run["returncode"] != 0:
                raise ValueError(f"baseline did not produce the upstream output: {guest}")
            yield (language, row["profile"], engine, guest, owner, interface, run["argv"], expected, case)


def stage_passed(stage, interface, returncode, stdout, stderr, expected):
    """Check the VM decision, the affected import, and the observable guest output."""
    lines = ANSI.sub(b"", stderr).splitlines()
    name = interface.encode("ascii")
    if stage == "stdout-only":
        return returncode == 0 and stdout == expected and not any(b"host_denied_wasip1." + name + b"]" in line for line in lines)
    if stdout:
        return False
    if stage == "hidden":
        diagnostic = (b"Cannot link import 'wasi_snapshot_preview1'.'" + name +
                      b"' for single 'main': the interface exposure permission is hidden.")
        return returncode == 127 and any(diagnostic in line for line in lines)
    reason = {"deny": b"interface calls are not allowed.",
              "allow-without-grant": b"operation or resource authority was not granted."}[stage]
    decision = b"wasip1." + name + b" denied for single 'main': " + reason
    tag = b"[host_denied_wasip1." + name + b"]"
    return returncode == 0 and any(decision in line and tag in line for line in lines)


def measure(args, task):
    language, profile, engine, guest, owner, interface, original, expected, case = task
    directory = args.work / profile / language / engine
    directory.mkdir(parents=True)
    rows = []
    for stage in STAGES:
        argv = policy(original, guest, owner, args.vm, interface, stage)
        row = dict(language=language, profile=profile, engine=engine, case=case, stage=stage,
                   interface=interface, argv=argv, guest_sha256=digest(guest), owner_sha256=digest(owner) if owner else None)
        try:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=args.timeout)
            stdout, stderr = proc.stdout, proc.stderr
            row["returncode"] = proc.returncode
            row["passed"] = stage_passed(stage, interface, proc.returncode, stdout, stderr, expected)
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
            row.update(passed=False, timeout_seconds=args.timeout)
        for suffix, data in (("out", stdout), ("err", stderr)):
            (directory / (stage + "." + suffix)).write_bytes(data)
            row[suffix + "_sha256"] = hashlib.sha256(data).hexdigest()
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("external", "objc", "vm", "work"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    add_vm_identity_options(parser)
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout < 1:
        parser.error("jobs and timeout must be positive")
    vm = verified_vm(args)
    tasks = [*select_rows(args.external, False, vm), *select_rows(args.objc, True, vm)]
    if len({(t[0], t[1], t[2]) for t in tasks}) != 128 or len(tasks) != 128:
        parser.error("expected four languages, sixteen profiles, and two engines")
    args.work.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    with ThreadPoolExecutor(args.jobs) as pool, (args.work / "results.jsonl").open("x") as log:
        for batch in pool.map(lambda item: measure(args, item), tasks):
            for row in batch:
                print(json.dumps(row), file=log, flush=True)
                counts["pass" if row["passed"] else "failed"] += 1
    summary = {"vm": vm, "plans": len(tasks) * len(STAGES), "outcomes": counts,
               "sources": {str(p): digest(p / "results.jsonl") for p in (args.external, args.objc)}}
    (args.work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return int(counts["failed"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
