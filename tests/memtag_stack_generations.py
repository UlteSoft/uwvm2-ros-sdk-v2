"""Run compiler-produced stack generation and benign pointer-observation tests."""
import argparse
import json
from pathlib import Path
import subprocess
import resource
import os

from separate_compilation import ROOT, Profile, cgroup_record, sha
from memtag_performance import exported_index
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("toolchain", "runtime", "work"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    tool = (args.toolchain / "bin").resolve()
    vm = args.runtime.resolve()
    work = args.work.resolve()
    group = cgroup_record()
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    fixtures = ROOT / "tools/wasm/memtag"
    ir = fixtures / "memtag-lifetime-generations.ll"
    observer = fixtures / "memtag-lifetime-observer.c"
    receipt = {"complete": False, "cgroup": group, "inputs": {str(p): sha(p) for p in
               (Path(__file__), tool / "llc", tool / "clang", tool / "wasm-ld", tool / "FileCheck", vm, ir, observer)}, "cases": []}

    def save():
        (work / "results.json").write_text(json.dumps(receipt, indent=2) + "\n")

    def run(case, command):
        result = subprocess.run(command, capture_output=True, timeout=180, cwd=work)
        (work / (case + ".log")).write_bytes(result.stdout + result.stderr)
        receipt["cases"].append(dict(case=case, code=result.returncode,
                                     command=[str(v) for v in command]))
        save()
        result.check_returncode()

    save()
    for width, period in ((32, 16), (64, 256)):
        ident = str(width)
        guest = f"wasm{width}-unknown-unknown"
        selection = [tool / "llc", "-mtriple=" + guest, "-mattr=+memtag", "-verify-each"]
        many = work / ("many-" + ident + ".ll")
        source = ["declare void @record(i32, ptr) nounwind", "define void @many() sanitize_memtag {", "entry:"]
        # Each registered object stays live until return. The observer checks
        # actual address neighbors across a frame larger than the tag alphabet.
        source.extend(f"  %a{i} = alloca [16 x i8], align 16" for i in range(period + 1))
        source.extend(f"  call void @record(i32 {i}, ptr %a{i})" for i in range(period + 1))
        source.extend(("  ret void", "}"))
        many.write_text("\n".join(source) + "\n")
        mir = work / ("many-" + ident + ".mir")
        run("object-ir-" + ident, [*selection, "-stop-after=wasm-stack-tagging", many, "-o", mir])
        checks = work / ("many-" + ident + ".check")
        checks.write_text(f"; CHECK-LABEL: define void @many(\n; CHECK-COUNT-{period+1}: = call ptr @llvm.wasm.memtag.claim.i{width}(\n; CHECK: ret void\n")
        run("registered-stack-objects-" + ident, [tool / "FileCheck", checks, "--implicit-check-not=@llvm.wasm.memtag.hint", "--implicit-check-not=@llvm.wasm.memtag.random", "--input-file=" + str(mir)])
        objects = []
        for name, path in (("many", many), ("lifetimes", ir)):
            obj = work / (name + ident + ".o")
            run(name + "-obj-" + ident, [*selection, "-O3", "-filetype=obj", path, "-o", obj])
            objects.append(obj)
        obs = work / ("observer" + ident + ".o")
        run("observer-" + ident, [tool / "clang", "--no-default-config", "--target=" + guest, "-fsanitize=memtag",
                                   "-ffreestanding", "-nostdlib", "-O3", "-g", "-c", observer, "-o", obs])
        app = work / ("stack" + ident + ".wasm")
        link = [tool / "wasm-ld", "-m", f"wasm{width}", "--no-entry", "--export=check_stack_generations", *objects, obs, "-o", app]
        run("link-" + ident, link)
        if inspect(app.read_bytes()):
            raise ValueError("expected a fully freestanding Wasm application")
        receipt["inputs"][str(app)] = sha(app)
        entry = str(exported_index(app, "check_stack_generations"))
        for engine in ("int", "aot"):
            for enabled in (True, False):
                flags = [] if enabled else ["--runtime-disable-memtag"]
                run(f"{ident}-{engine}-runtime-{'on' if enabled else 'off'}",
                    [vm, *Profile(width).uwvm_feature_flags(), *flags, "--runtime-" + engine, "--runtime-compile-threads", "0",
                     "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-start-func", entry, str(int(enabled)), "--run", app])
    receipt["complete"] = True
    save()


if __name__ == "__main__":
    main()
