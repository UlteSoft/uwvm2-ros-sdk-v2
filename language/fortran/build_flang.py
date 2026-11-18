"""Build an SDK Flang host executable with only the WebAssembly target backend."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools/wasm/memtag"))
from build_producer import checked, prepare
from build_sysroots import diagnostics_overlay

from flang_identity import (ABI_PATCH, ADDRESS_KIND_PATCH, ASSUMED_EXTENT_PATCH, GLOBALS_HEADER_PATCH,
                            LLVM_RECIPE_SHA256, identity, llvm_recipe_digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", required=True, type=Path, help="native Clang and LLD prefix")
    parser.add_argument("--source-work", required=True, type=Path, help="SDK LLVM source cache work tree")
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="path to the installed host flang")
    parser.add_argument("--configure-only", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    try:
        if args.jobs < 1:
            raise ValueError("--jobs must be positive")
        bootstrap = args.bootstrap.resolve(strict=True)
        work = args.work.resolve()
        output = args.output.resolve()
        if work == ROOT or work in ROOT.parents:
            raise ValueError("--work must be a dedicated build directory")
        work.mkdir(parents=True, exist_ok=True)
        entry = json.loads((ROOT / "tools/wasm/memtag/source-lock.json").read_bytes())["sources"]["llvm-23.1.5"]
        if llvm_recipe_digest(entry) != LLVM_RECIPE_SHA256:
            raise ValueError("Flang target patch needs requalification with the selected LLVM source")
        source = prepare(entry, args.source_work.resolve(), None)
        # LLVM resolves sibling projects as llvm/../flang and llvm/../clang.
        # Apply the LLVM-side change last so that llvm is a physical directory
        # inside the final overlay alongside the fully patched siblings.
        for patch in (ABI_PATCH, ASSUMED_EXTENT_PATCH, ADDRESS_KIND_PATCH, GLOBALS_HEADER_PATCH):
            source = diagnostics_overlay(source, patch, work)
        if not (source / "llvm" / "..").samefile(source):
            raise ValueError("LLVM would resolve sibling projects outside the final Flang source overlay")
        build = work / "build"
        log = work / "build.log"
        config = {"CMAKE_BUILD_TYPE": "Release", "CMAKE_CXX_COMPILER": bootstrap / "bin/clang++",
                  "CMAKE_C_COMPILER": bootstrap / "bin/clang", "CMAKE_DISABLE_PRECOMPILE_HEADERS": "ON",
                  "CMAKE_C_FLAGS_RELEASE": "-O3 -g", "CMAKE_CXX_FLAGS_RELEASE": "-O3 -g",
                  "CMAKE_EXE_LINKER_FLAGS": "-fuse-ld=" + str(bootstrap / "bin/ld.lld"),
                  "LLVM_ENABLE_PROJECTS": "clang;mlir;flang", "LLVM_TARGETS_TO_BUILD": "WebAssembly",
                  "LLVM_DEFAULT_TARGET_TRIPLE": "wasm32-unknown-wasip1", "LLVM_ENABLE_ASSERTIONS": "ON",
                  "LLVM_PARALLEL_LINK_JOBS": "1", "LLVM_ENABLE_ZLIB": "OFF", "LLVM_ENABLE_ZSTD": "OFF",
                  "LLVM_ENABLE_BINDINGS": "OFF", "LLVM_INCLUDE_TESTS": "OFF", "LLVM_INCLUDE_EXAMPLES": "OFF",
                  "LLVM_INCLUDE_BENCHMARKS": "OFF", "LLVM_INCLUDE_DOCS": "OFF",
                  "FLANG_INCLUDE_TESTS": "OFF", "CLANG_INCLUDE_TESTS": "OFF", "MLIR_INCLUDE_TESTS": "OFF",
                  "LLVM_APPEND_VC_REV": "OFF", "Python3_EXECUTABLE": sys.executable}
        checked(["cmake", "-G", "Ninja", "-S", str(source / "llvm"), "-B", str(build),
                 *(f"-D{k}={v}" for k,v in config.items())], log)
        if args.configure_only:
            return 0
        checked(["cmake", "--build", str(build), "--parallel", str(args.jobs), "--target", "flang", "llvm-config"], log)
        targets = subprocess.check_output([build / "bin/llvm-config", "--targets-built"], text=True).split()
        if targets != ["WebAssembly"]:
            raise ValueError("Flang build contains unexpected code generators")
        binary = build / "bin/flang"
        with tempfile.TemporaryDirectory(dir=work) as td:
            probe = Path(td) / "probe.f90"
            probe.write_text("function answer() bind(c)\ninteger(4) answer\nanswer=kind(sizeof(1))\nend function\n")
            for bits in (32, 64):
                obj = Path(td) / f"w{bits}.o"
                checked([str(binary), "-fc1", "-triple", f"wasm{bits}-unknown-wasip1",
                         "-emit-obj", str(probe), "-o", str(obj)], log)
                if obj.read_bytes()[:8] != b"\0asm\1\0\0\0":
                    raise ValueError("Flang did not generate a Wasm object")
                ir = Path(td) / f"w{bits}.ll"
                checked([str(binary), "-fc1", "-triple", f"wasm{bits}-unknown-wasip1",
                         "-emit-llvm", "-O3", str(probe), "-o", str(ir)], log)
                if not re.search(rf"\bret i32 {bits // 8}\b", ir.read_text()):
                    raise ValueError("Flang C_SIZEOF result kind disagrees with the target pointer width")
            native_obj = Path(td) / "native.o"
            native = subprocess.run([binary, "-fc1", "-triple", "x86_64-unknown-linux-gnu",
                "-emit-obj", probe, "-o", native_obj], capture_output=True)
            if native.returncode == 0 or (native_obj.is_file() and native_obj.stat().st_size):
                raise ValueError("Flang unexpectedly generated a native object")
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as install:
            staged = Path(install) / output.name
            shutil.copy2(binary, staged)
            record = staged.with_name(staged.name + ".json")
            record.write_text(json.dumps(identity(staged), indent=2) + "\n")
            os.replace(staged, output)
            os.replace(record, output.with_name(output.name + ".json"))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, RuntimeError) as exc:
        parser.exit(1, f"build_flang: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
