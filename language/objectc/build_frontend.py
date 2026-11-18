#!/usr/bin/env python3
"""Rebuild the GNUstep Objective-C Wasm frontend from the SDK's locked LLVM."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "install"))
sys.path.insert(0, str(ROOT / "tools/wasm/memtag"))
from build_producer import prepare
from compiler import digest
import runtime

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", required=True, type=Path, help="native compiler used to build the host frontend")
    parser.add_argument("--source-work", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="e.g. TOOLCHAIN/bin/wros-objc-clang")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    try:
        if not 1 <= args.jobs <= 32: raise ValueError("--jobs must be between 1 and 32")
        host = args.bootstrap.resolve(strict=True) / "bin"
        lock = json.loads((ROOT/"tools/wasm/memtag/source-lock.json").read_bytes())["sources"]["llvm-23.1.5"]
        if lock["revision"] != runtime.FRONTEND_REVISION:
            raise ValueError("the Objective-C ABI changes require review with this LLVM revision")
        for name in runtime.PATCHES:
            p=runtime.VENDOR/name
            lock["patches"].append({"path":p.relative_to(ROOT).as_posix(),"sha256":digest(p)})
        source = prepare(lock, args.source_work.resolve(), None)
        build = args.work.resolve()/"objc-clang-build"
        out = args.output.absolute()
        if out.exists() or out.with_name(out.name+".json").exists():
            raise ValueError("compiler output already exists")
        settings={"CMAKE_BUILD_TYPE":"Release", "CMAKE_C_COMPILER":host/"clang", "CMAKE_CXX_COMPILER":host/"clang++",
                  "CMAKE_EXE_LINKER_FLAGS":"-fuse-ld="+str(host/"ld.lld"),
                  "CMAKE_C_FLAGS_RELEASE":"-O3 -g -DNDEBUG","CMAKE_CXX_FLAGS_RELEASE":"-O3 -g -DNDEBUG",
                  "LLVM_ENABLE_PROJECTS":"clang","LLVM_TARGETS_TO_BUILD":"WebAssembly","LLVM_ENABLE_ASSERTIONS":"ON",
                  "LLVM_DEFAULT_TARGET_TRIPLE":"wasm32-wasip1","LLVM_INCLUDE_TESTS":"OFF","LLVM_INCLUDE_EXAMPLES":"OFF",
                  "LLVM_INCLUDE_BENCHMARKS":"OFF","LLVM_PARALLEL_LINK_JOBS":"1","CLANG_PLUGIN_SUPPORT":"OFF",
                  "CMAKE_DISABLE_PRECOMPILE_HEADERS":"ON"}
        subprocess.run(["cmake","-G","Ninja","-S",source/"llvm","-B",build,*[f"-D{k}={v}" for k,v in settings.items()]],check=True)
        subprocess.run(["cmake","--build",build,"--target","clang","--parallel",str(args.jobs)],check=True)
        compiler=build/"bin/clang"
        targets=subprocess.check_output([compiler,"--print-targets"],text=True)
        if {line.partition(" - ")[0].strip() for line in targets.splitlines() if " - " in line} != {"wasm32","wasm64"}:
            raise ValueError("Objective-C frontend includes an unexpected backend")
        out.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=out.parent) as td:
            temp=Path(td)/"compiler";shutil.copy2(compiler,temp)
            marker=temp.with_name("compiler.json")
            marker.write_text(json.dumps(runtime.frontend_record(temp),indent=2)+"\n")
            os.link(temp,out)
            os.link(marker,out.with_name(out.name+".json"))
    except (ValueError,KeyError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
        parser.exit(1,f"{parser.prog}: {exc}\n")

if __name__=="__main__": main()
