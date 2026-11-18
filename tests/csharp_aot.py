"""Run actual Roslyn and Mono LLVMOnly output in both VM engines.

This component regression compiles two managed methods that need no CLR state.
The managed-array control checks the actual unresolved CLR dependency.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shlex
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "language/csharp"))
from host import environment, LOCK, REF_PACK, SDK_VERSION, sha, stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dotnet", "mono-compiler", "extract", "toolchain", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--sdk", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host-cxx", type=Path, default=Path("/usr/bin/g++"))
    args = parser.parse_args()
    sdk = args.sdk.resolve()
    sys.path[:0] = [str(sdk / "install"), str(sdk / "tests")]
    from frontend import audit
    from guest_profile import Profile
    from imports import inspect
    from memtag_performance import exported_index
    from separate_compilation import cgroup_record

    group = cgroup_record()
    work = args.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    tool = args.toolchain.resolve() / "bin"
    fixtures = Path(__file__).with_name("csharp")
    lock = LOCK
    staging = work / "inputs"
    verified = stage(work, args.dotnet.resolve(), args.mono_compiler.resolve())
    host = staging / "dotnet"
    compiler = staging / "compiler"
    aot = compiler / "bin/mono-aot-cross"
    roslyn = host / "sdk" / SDK_VERSION / "Roslyn/bincore/csc.dll"
    refs = host / "packs/Microsoft.NETCore.App.Ref" / REF_PACK / "ref/net9.0"
    runtime = args.runtime.resolve()
    extract = args.extract.resolve()
    src = fixtures / "Body.cs"
    check = fixtures / "check.c"
    marker = sdk / "tools/wasm/tag_ir.cpp"
    inputs = [Path(__file__), sdk / "language/csharp/host.py", src, check, marker, tool / "llvm-config", tool / "clang",
              tool / "wasm-ld", tool / "llvm-objdump", aot, roslyn, extract,
              runtime, lock, tool / "opt", args.host_cxx.resolve()]
    report = dict(complete=False, cgroup=group, scope="freestanding C# methods",
                  inputs={str(p): sha(p) for p in inputs}, managed_files=verified, steps=[], modules={})
    def save():
        (work / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    env = environment(work, tool)

    def run(label, argv, expected_failure=None):
        cmd = list(map(str, argv))
        environment = env
        if Path(cmd[0]) == aot:
            environment = dict(env, LD_LIBRARY_PATH=str(compiler / "lib"))
        elif Path(cmd[0]) == extract:
            environment = dict(env, LD_LIBRARY_PATH=os.pathsep.join(
                [str(extract.parents[1] / "lib/x86_64-unknown-linux-gnu"), str(extract.parents[1] / "lib")]))
        result = subprocess.run(cmd, cwd=work, env=environment, capture_output=True, timeout=150)
        trace = result.stdout + result.stderr
        (work / (label + ".log")).write_bytes(trace)
        report["steps"].append(dict(name=label, exit=result.returncode, argv=cmd))
        save()
        if expected_failure is None:
            result.check_returncode()
        elif result.returncode == 0 or expected_failure not in trace:
            raise ValueError("missing expected diagnostic: " + label)
        return result.stdout.decode(errors="replace")

    save()
    dll = work / "Body.dll"
    bc = work / "Body.bc"
    references = [refs / name for name in ("mscorlib.dll", "System.Runtime.dll", "netstandard.dll")]
    run("csharp-il", [host / "dotnet", roslyn, "-nologo", "-deterministic+", "-target:library",
                      "-unsafe+", "-optimize+", "-nostdlib+", *["-reference:" + str(p) for p in references],
                      "-out:" + str(dll), src])
    run("managed-aot", [aot, "--debug", "--aot=llvmonly,asmonly,static,llvm-outfile=" + str(bc), dll])
    run("closure", [extract, "--recursive", "--func=Body_Body_TagNeighbors_int",
                    "--func=Body_Body_Rotate_int", bc, "-o", "numeric.bc"])
    run("managed-array", [extract, "--recursive", "--func=Body_Body_ManagedArray_int", bc, "-o", "array.bc"])
    flags = shlex.split(run("llvm-libraries", [tool / "llvm-config", "--cxxflags", "--ldflags", "--libs",
                                               "irreader", "bitwriter", "core", "support", "--system-libs"]))
    run("marker", [args.host_cxx, "-O3", "-g", marker, *flags, "-o", "mark"])
    common = [tool / "clang", "--no-default-config", "--target=wasm32-wasip1", "-O3", "-g", "-nostdlib",
              "-ffreestanding", "-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false"]
    for enabled in (True, False):
        name = "mte" if enabled else "plain"
        module = work / (name + ".wasm")
        profile = Profile(32, mte=enabled)
        run(name + "-annotate", [work / "mark", "--mte" if enabled else "--no-mte",
                                 "numeric.bc", name + ".bc"])
        cc = common + (["-fsanitize=memtag"] if enabled else [])
        run(name + "-compile", [*cc, "-c", name + ".bc", "-o", name + ".o"])
        run(name + "-observer", [*cc, "-c", check, "-o", "check.o"])
        run(name + "-link", [tool / "wasm-ld", "--fatal-warnings", "--no-entry", "--export=check",
                             name + ".o", "check.o", "-o", module])
        audit(module.read_bytes(), profile)
        if inspect(module.read_bytes()):
            raise ValueError("unexpected import in a freestanding C# computation")
        asm = run(name + "-asm", [tool / "llvm-objdump", "-d", name + ".o"])
        count = 2 if enabled else 0
        if asm.count("memtag.claim") != count or asm.count("memtag.release") != count:
            raise ValueError("unexpected managed stack allocation lifecycle")
        entry = str(exported_index(module, "check"))
        for engine in ("int", "aot"):
            run(name + "-" + engine, [runtime, *profile.uwvm_feature_flags(),
                "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path",
                "disable", "--runtime-memtag-mode", "sync", *([] if enabled else ["--runtime-disable-memtag"]),
                "--wasm-set-start-func", entry, str(int(enabled)), "--run", module])
        report["modules"][name] = sha(module)
    run("array-annotate", [work / "mark", "--mte", "array.bc", "array-mte.bc"])
    run("array-codegen", [*common, "-fsanitize=memtag", "-c", "array-mte.bc", "-o", "array.o"])
    run("array-no-runtime", [tool / "wasm-ld", "--no-entry", "--export=Body_Body_ManagedArray_int",
                             "array.o", "-o", "array.wasm"], b"undefined symbol: mono_aot_file_info")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
