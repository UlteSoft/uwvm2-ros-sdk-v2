"""Check the source lock against real compiler output before building target libraries."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from separate_compilation import ROOT, cgroup_record, sha

sys.path.insert(0, str(ROOT / "tools/wasm/memtag"))
from build_sysroots import require_allocation_policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-toolchain", type=Path, required=True)
    parser.add_argument("--candidate-toolchain", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    work = args.output.resolve()
    if not work.is_relative_to(ROOT / ".tmp"):
        parser.error("choose a new SDK .tmp output")
    work.mkdir(exist_ok=False, parents=True)
    lock = ROOT / "tools/wasm/memtag/source-lock.json"
    policy = json.loads(lock.read_bytes())["producer"]["allocation_policy"]
    result = dict(complete=False, cgroup=cgroup_record(), inputs={str(lock): sha(lock)}, cases=[])
    def check(label, asm, bits, accepted):
        try:
            require_allocation_policy(asm, policy, bits)
        except ValueError:
            if accepted:
                raise
        else:
            if not accepted:
                raise RuntimeError(label + " unexpectedly passed")
        result["cases"].append(dict(name=label, accepted=accepted))
        (work / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    for bits in (32, 64):
        for index, (ops, good) in enumerate((
                (["claim", "release"], True), (["claimz", "release"], True),
                (["reserve", "activate", "release"], True), (["reserve", "release"], False),
                (["claim"], False), (["release"], False), (["release", "claim"], False),
                (["claim", "release", "release"], False), (["randomstorez", "store"], False),
                (["claim", "randomstore", "release"], False), ([], False))):
            check(f"syntax-{bits}-{index}", "".join("  memtag." + op + " 0\n" for op in ops), bits, good)
        for kind, toolchain, good in (("old", args.old_toolchain, False), ("candidate", args.candidate_toolchain, True)):
            if toolchain is None:
                continue
            compiler = toolchain.resolve() / "bin/clang"
            result["inputs"][str(compiler)] = sha(compiler)
            cmd = [compiler, "--no-default-config", f"--target=wasm{bits}-wasip1", "-O3", "-g", "-x", "c", "-S",
                   "-fsanitize=memtag", "-o", "-", "-"]
            assembly = subprocess.check_output(cmd, text=True, input="extern void observe(void *); "
                                               "void example(void) { char region[64]; observe(region); }", timeout=30)
            (work / (kind + str(bits) + ".s")).write_text(assembly)
            check(kind + str(bits), assembly, bits, good)
    result["complete"] = True
    (work / "results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
