"""Exercise each possible logical tag difference through real SDK-compiled loads and stores."""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import subprocess

from memtag_performance import exported_index
from separate_compilation import Profile, ROOT, cgroup_record, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--sysroots", required=True, action="append", type=Path)
    parser.add_argument("--exceptions", choices=("eh", "noeh"), default="eh")
    parser.add_argument("--candidate-mte", action="store_true",
                        help="use an SDK frontend's explicit --legacy-mte switch to measure a candidate")
    args = parser.parse_args()
    group = cgroup_record()
    work = args.output.resolve()
    if not work.is_relative_to(ROOT / ".tmp"):
        parser.error("choose a fresh SDK .tmp directory")
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    source = [ROOT / "tests/memtag" / name for name in ("tag_access.c", "tag_access_word.c", "allocation_lifecycle.c")]
    wrapper = ROOT / "bin/wrc"
    tool = args.toolchain.resolve()
    objdump = tool / "bin/llvm-objdump"
    runtime = args.runtime.resolve()
    inputs = [Path(__file__), *source, wrapper, tool / "bin/clang", tool / "bin/wasm-ld",
              objdump, *args.sysroots, runtime]
    result = dict(complete=False, cgroup=group, inputs={str(p): sha(p) for p in inputs},
                  builds=[], groups=[], allocator=[], scope="Default-instrumented C stack, scalar reads and writes, heap tag lifecycle, software synchronous MTE.")

    def save():
        partial = work / "results.part"
        partial.write_text(json.dumps(result, indent=2) + "\n")
        partial.replace(work / "results.json")

    save()
    for bits, tag_bits in ((32, 4), (64, 8)):
        guest = work / f"word{bits}.wasm"
        roots = [arg for path in args.sysroots for arg in ("--sysroots", path.resolve())]
        profile = Profile(bits, exceptions=args.exceptions)
        flags = (["--legacy-mte"] if args.candidate_mte else []) + (["--no-eh"] if args.exceptions == "noeh" else [])
        command = list(map(str, [wrapper, "--toolchain", tool, *roots, *flags,
            "--target", f"wasm{bits}", "--reactor", "--export", "check_access", "--export", "check_word", "--export", "check_lifecycle", "--export", "page_size_constant",
            "-O3", "-g", *source, "-o", guest]))
        subprocess.run(command, cwd=work, check=True, timeout=90)
        asm = subprocess.check_output([objdump, "-d", guest], text=True, timeout=30)
        (work / f"word{bits}.asm").write_text(asm)
        functions = re.split(r"(?m)^[0-9a-f]+ <([^>]+)>:\s*$", asm)
        body = dict(zip(functions[1::2], functions[2::2]))
        access = body["check_access"]
        legacy = bool(re.search(r"\bmemtag\.randomstorez?\b", access) and "memtag.store" in access)
        owner = bool(re.search(r"\bmemtag\.(claimz?|reserve)\b", access) and "memtag.release" in access)
        if not (legacy or owner):
            raise ValueError("escaping stack allocation lacks tag generation or retirement")
        if "memtag.load" in body["page_size_constant"]:
            raise ValueError("numeric linker value performs an allocation-tag lookup")
        for instruction in ("memtag.insert", "memtag.load", "i32.load", "i32.store"):
            if instruction not in body["check_word"]:
                raise ValueError("missing tested operation: " + instruction)
        entry = exported_index(guest, "check_access")
        result["builds"].append(dict(bits=bits, argv=command, sha256=sha(guest), entry=entry))
        for engine in ("int", "aot"):
            base = [str(runtime), *profile.uwvm_feature_flags(), "--runtime-" + engine,
                    "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                    "--runtime-memtag-backend", "software", "--runtime-memtag-mode", "sync",
                    "--debug-fault-action", "exit", "--log-color", "disable", "--wasm-set-main-module-name", "main", "--wasm-set-start-func", str(entry)]
            lifecycle = base[:-1] + [str(exported_index(guest, "check_lifecycle")), "--run", str(guest)]
            proc = subprocess.run(lifecycle, cwd=work, capture_output=True, timeout=20)
            (work / f"allocator-{bits}-{engine}.log").write_bytes(proc.stdout + proc.stderr)
            result["allocator"].append(dict(bits=bits, engine=engine, exit=proc.returncode))
            save()
            proc.check_returncode()
            for store in (False, True):
                for cross in (False, True):
                    # Exercise the entire difference domain on ordinary accesses.
                    # A straddling access changes only the second granule; isolate each tag bit there.
                    deltas = range(1 << tag_bits) if not cross else [0, *(1 << i for i in range(tag_bits)), (1 << tag_bits) - 1]
                    row = dict(engine=engine, bits=bits, operation="write" if store else "read", straddles=cross,
                               same_tag_passes=0, mismatch_traps=0)
                    result["groups"].append(row)
                    for delta in deltas:
                        cmd = base + [str(delta), str(int(store)), str(int(cross)), "--run", str(guest)]
                        proc = subprocess.run(cmd, cwd=work, capture_output=True, timeout=20)
                        log = (proc.stdout + proc.stderr).decode(errors="replace")
                        if delta == 0:
                            accepted = proc.returncode == 0
                        else:
                            logical = re.search(r"^  Pointer tag: (\d+)$", log, re.M)
                            memory = re.search(r"^  Allocation tag: (\d+)$", log, re.M)
                            accepted = (logical and memory and (int(logical[1]) ^ int(memory[1])) == delta and
                                        proc.returncode == 122 and "uwvm: [crash] memory-protection" in log and
                                        "Reason: memory tag mismatch" in log and "Exit status: 122" in log)
                        if not accepted:
                            row["failed"] = dict(delta=delta, argv=cmd, exit=proc.returncode, output=log)
                            save()
                            raise RuntimeError(f"unexpected outcome for {bits}/{engine}/{store}/{cross}/{delta}: {log[-750:]}")
                        row["same_tag_passes" if delta == 0 else "mismatch_traps"] += 1
                        if delta == 1:
                            (work / f"mismatch-{bits}-{engine}-{int(store)}-{int(cross)}.log").write_text(log)
                    save()
    result["complete"] = all(sha(Path(p)) == h for p, h in result["inputs"].items())
    save()
    if not result["complete"]:
        raise RuntimeError("qualification inputs changed during execution")
    print(f"{sum(g['same_tag_passes'] + g['mismatch_traps'] for g in result['groups'])} VM executions passed")


if __name__ == "__main__":
    main()
