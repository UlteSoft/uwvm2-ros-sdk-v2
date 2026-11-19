"""Build actual F# assembly methods and verify their final Wasm and ROS authority."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from separate_compilation import Profile, cgroup_record, sha
from artifacts import sections
from bootstrap import Source, install
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "dotnet", "mono-compiler", "toolchain", "vm", "xmake", "output"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    report = dict(complete=False, cgroup=cgroup_record(), commit=args.commit, vm=sha(args.vm), cases=[], products={})
    def save():
        (out/"results.json").write_text(json.dumps(report, indent=2)+"\n")

    source = Source(args.commit, args.repository)
    result = install(source, "unitree", "fsharp", out/"install", [])
    sdk = Path(result["directory"])
    adapters = {p for p in source.requested if p.endswith(("/adapter.lua", "/platform.lua"))}
    if adapters != {"language/fsharp/xmake/adapter.lua", "platform/unitree/xmake/platform.lua"}:
        raise ValueError("unexpected installer selection")
    tools = ["sdk/10.0.404/FSharp/fsc.dll", "sdk/10.0.404/FSharp/FSharp.Core.dll"]
    report["inputs"] = {str(p):sha(p) for p in (sdk/"bin/wrfs", args.mono_compiler/"bin/mono-aot-cross",
                        args.toolchain/"bin/clang", *(args.dotnet/n for n in tools))}
    report["installation"] = result
    env = dict(PATH="/usr/bin:/bin", LC_ALL="C", HOME=os.environ["HOME"], UWVM_ROS_SDK_ROOT=str(sdk),
               WROS_PLATFORM="unitree", WROS_DOTNET=str(args.dotnet), WROS_MONO=str(args.mono_compiler),
               WROS_TOOLCHAIN=str(args.toolchain), XMAKE_GLOBALDIR=str(out/"xmake-global"),
               TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    project = out/"project"
    shutil.copytree(sdk/"examples/fsharp/scene-abi", project)
    def run(name, argv, refusal=None):
        command = list(map(str, argv))
        proc = subprocess.run(command, cwd=project, env=env, capture_output=True, timeout=150)
        log = out/(name+".log")
        log.write_bytes(proc.stdout+proc.stderr)
        passed = proc.returncode == 0 if refusal is None else proc.returncode != 0 and refusal in log.read_bytes()
        report["cases"].append(dict(name=name, exit=proc.returncode, expected_success=refusal is None,
                                    passed=passed, argv=command, log=sha(log)))
        save()
        if not passed:
            raise ValueError(name+": "+log.read_text(errors="replace")[-1000:])

    def vm(engine):
        return [args.vm, *Profile().uwvm_feature_flags(), "--runtime-"+engine, "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit", "--runtime-memtag-mode", "sync"]

    cli = [sdk/"bin/wrfs", "--dotnet",args.dotnet,"--mono-compiler",args.mono_compiler,"--toolchain",args.toolchain]
    sample = project/"Robot.fs"
    direct = out/"direct.wasm"
    run("configure",[args.xmake, "f","-c","-y","-a","wasm32"])
    run("build",[args.xmake,"-j1","robot"])
    installed, = (project/"build").rglob("robot.wasm")
    run("cli",[*cli,"--scene-entry","Robot.Start",sample,"-o",direct])
    plain = out/"plain.wasm"
    run("plain",[*cli,"--no-mte","--scene-entry","Robot.Start",sample,"-o",plain])
    for name, module in (("xmake",installed),("cli",direct),("plain",plain)):
        data = module.read_bytes()
        if inspect(data) != [{"module":"uwvm_ros_v2","name":"abi","kind":0,"params":[],"results":["i32"]}]:
            raise ValueError("unexpected ROS or WASI import")
        if [data[start] for start,_,_,_ in sections(data) if data[start]] != [1,2,3,7,10]:
            raise ValueError("unexpected state in a register-only ROS application")
        if b"WasmROS F# + Mono LLVMOnly" not in data or b"Robot.fs" not in data:
            raise ValueError("missing F# source attribution in Wasm")
        report["products"][name] = sha(module)
        for engine in ("int","aot"):
            base = [*vm(engine),"--wasm-set-main-module-name","main"]
            bind = ["--ros-scene-create","robot","--ros-scene-bind","robot","main","--ros-scene-interface","robot","abi"]
            run(name+"-"+engine+"-hidden",[*base,"--run",module],b"scene interface is hidden")
            run(name+"-"+engine+"-allowed",[*base,*bind,"allow","--run",module])
    kernel = project/"Kernel.fs"
    kernel.write_text("module Kernel\nlet Scale (n: int) = if n < 0 then n * 5 + 2 else n * 7 - 3\n")
    scalar = out/"scalar.wasm"
    run("scalar",[*cli,"--entry","Kernel.Scale",kernel,"-o",scalar])
    data = scalar.read_bytes()
    if inspect(data) or [data[start] for start,_,_,_ in sections(data) if data[start]] != [1,3,7,10]:
        raise ValueError("unexpected scalar module shape")
    report["products"]["scalar"] = sha(scalar)
    harness = project/"observe.c"
    harness.write_text('__attribute__((import_module("kernel"),import_name("evaluate"))) extern int evaluate(int);\n'
                       'void _start(void) { for (int n=-128;n<=128;++n) if(evaluate(n)!=(n<0?n*5+2:n*7-3)) __builtin_trap(); }\n')
    observer = out/"observer.wasm"
    run("observer",[args.toolchain/"bin/clang","--no-default-config","--target=wasm32-wasip1","-O3","-g",
                    "-ffreestanding","-nostdlib",harness,"-Wl,--no-entry,--export=_start","-o",observer])
    for engine in ("int","aot"):
        run("scalar-"+engine,[*vm(engine),"--wasm-preload-library",scalar,"kernel","--run",observer])
    destination = out/"existing.wasm"
    destination.write_bytes(b"known prior output")
    for name, body, error in (
        ("state","let mutable state = 2\nlet Scale(n:int) = n + state","needs the CLR"),
        ("heap","let Scale(n:int) = let items = Array.create n n in items.[0]","unsupported numeric IL operation"),
        ("script-reference",'#r "unapproved.dll"\nlet Scale(n:int) = n',"error FS"),
    ):
        kernel.write_text("module Kernel\n"+body+"\n")
        run("reject-"+name,[*cli,"--entry","Kernel.Scale",kernel,"-o",destination],error.encode())
    run("reject-legacy",[*cli,"--legacy-mte","--entry","Kernel.Scale",kernel,"-o",destination],b"statically checked")
    run("reject-component-target",[*cli,"--target","wasm32-wasip2","--entry","Kernel.Scale",kernel,"-o",destination],b"invalid choice")
    if destination.read_bytes()!=b"known prior output":
        raise ValueError("a rejected build replaced an existing module")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
