"""Verify the tags on cross-TU pointer initializers at an actual object boundary."""
import argparse
import json
import resource
import subprocess
from pathlib import Path

from separate_compilation import ROOT, Profile, cgroup_record, sha
from memtag_performance import exported_index
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("toolchain", "runtime", "work"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    group = cgroup_record()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    compiler = args.toolchain.resolve() / "bin/clang"
    linker = args.toolchain.resolve() / "bin/wasm-ld"
    vm = args.runtime.resolve()
    fixtures = [ROOT / "tests/memtag" / name for name in ("global_pointer_origins.c", "global_pointer_reader.c")]
    report = dict(complete=False, cgroup=group, cases=[],
                  inputs={str(p): sha(p) for p in (Path(__file__), compiler, linker, vm, *fixtures)})

    def save():
        (work / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, args):
        proc = subprocess.run(args, cwd=work, capture_output=True, timeout=90)
        (work / (name + ".log")).write_bytes(proc.stdout + proc.stderr)
        report["cases"].append(dict(name=name, args=[str(a) for a in args], code=proc.returncode))
        save()
        proc.check_returncode()

    save()
    for bits in (32, 64):
        objects = []
        for source in fixtures:
            obj = work / f"{source.stem}{bits}.o"
            run(obj.stem, [compiler, "--no-default-config", f"--target=wasm{bits}-unknown-unknown",
                           "-O3", "-g", "-ffreestanding", "-nostdlib", "-fsanitize=memtag",
                           "-c", source, "-o", obj])
            objects.append(obj)
        guest = work / f"origins{bits}.wasm"
        run(f"link{bits}", [linker, "-m", f"wasm{bits}", "--no-entry", "--export=check_pointer_origins",
                             *objects, "-o", guest])
        if inspect(guest.read_bytes()):
            raise ValueError("the fixture must be freestanding")
        report["inputs"][str(guest)] = sha(guest)
        entry = str(exported_index(guest, "check_pointer_origins"))
        for engine in ("int", "aot"):
            for enabled in (True, False):
                flags = [] if enabled else ["--runtime-disable-memtag"]
                run(f"wasm{bits}-{engine}-{int(enabled)}",
                    [vm, *Profile(bits).uwvm_feature_flags(), "--runtime-" + engine,
                     "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                     *flags, "--wasm-set-start-func", entry, str(int(enabled)), "--run", guest])
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
