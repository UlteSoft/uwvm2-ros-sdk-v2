"""Build the reviewed target error domains against a selected Wasm sysroot and execute them."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path[:0] = [str(SDK/"install"),str(SDK/"tests"),str(SDK/"tools/wasm/memtag")]
from build_producer import digest
from compiler import compiler_environment, make_command, select_closure
from guest_profile import Profile
from herbceptions_sysroot import definitions, install_domains
from imports import inspect
from separate_compilation import cgroup_record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm-source", "toolchain", "sysroots", "vm", "output"):
        p.add_argument("--"+name, required=True, type=Path)
    p.add_argument("--bits", type=int, choices=(32,64), default=32)
    p.add_argument("--eh", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--probe-legacy-abi", action="store_true",
                   help="also compile the patched libc++abi domain against a baseline sysroot without that domain")
    args = p.parse_args()
    out, tc = args.output.resolve(), args.toolchain.resolve(strict=True)
    env = compiler_environment(tc)
    report = dict(complete=False, scope="Portable error-domain code only", cgroup=cgroup_record(),
                  compiler=digest(tc/"bin/clang++"), vm=digest(args.vm), steps=[])
    out.mkdir(parents=True,exist_ok=False)
    def save():
        (out/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    def run(name, argv, diagnostic=None):
        cmd = list(map(str,argv))
        proc = subprocess.run(cmd,cwd=out,env=env,capture_output=True,timeout=300)
        logs = proc.stdout+proc.stderr
        (out/(name+".log")).write_bytes(logs)
        ok = proc.returncode == 0 if diagnostic is None else proc.returncode != 0 and diagnostic in logs
        report["steps"].append(dict(name=name,exit=proc.returncode,expected_success=diagnostic is None,
                                    passed=ok,argv=cmd))
        save()
        if not ok:
            raise RuntimeError(name+": "+logs.decode(errors="replace")[-1800:])
    profile = Profile(address_bits=args.bits, exceptions="eh" if args.eh else "noeh")
    _, _, _, sysroot, resource = select_closure([args.sysroots], profile, digest(tc/"bin/clang++"))
    triple = profile.triple
    source = args.llvm_source.resolve(strict=True) / "libherbceptions"
    report["source_tree"] = {str(f.relative_to(source)):digest(f) for f in sorted(source.rglob("*")) if f.is_file()}
    compiler_flags = ["-O3", "-g", "-fsanitize=memtag", "-resource-dir="+str(resource), *profile.llvm_feature_flags()]
    targets = dict(CMAKE_SYSTEM_NAME="WASI",CMAKE_SYSTEM_PROCESSOR="wasm"+str(args.bits),
                   CMAKE_CXX_COMPILER_TARGET=triple,CMAKE_CXX_COMPILER=str(tc/"bin/clang++"),
                   CMAKE_AR=str(tc/"bin/llvm-ar"),CMAKE_RANLIB=str(tc/"bin/llvm-ranlib"),CMAKE_TRY_COMPILE_TARGET_TYPE="STATIC_LIBRARY")
    options = definitions(sysroot," ".join(compiler_flags),targets)
    build, stage = out/"build", out/"stage"
    run("configure", ["/usr/bin/cmake","-G","Ninja","-S",source,"-B",build,"-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX="+str(stage), *["-D"+k+"="+v for k,v in options.items()]])
    run("build", ["/usr/bin/cmake","--build",build,"--parallel","2"])
    run("install", ["/usr/bin/cmake","--install",build])
    publish = out/"checked"
    row = install_domains(stage,publish,triple,tc)
    report["domain_archive"] = row
    guest = out/"domains.wasm"
    link, _ = make_command(tc,[args.sysroots],profile,"cpp",["-O3","-g","-std=c++23","-mexec-model=reactor",
        "-Wl,--no-entry,--export=_start","-I"+str(publish/"include"),str(HERE/"domains.cpp"),str(publish/row["archive"]),"-o",str(guest)],verify=True)
    run("link",link)
    if inspect(guest.read_bytes()):
        raise ValueError("domain guest unexpectedly imports host capabilities")
    report["wasm_sha256"]=digest(guest)
    for engine in ("int","aot"):
        run(engine, [args.vm.resolve(),*profile.uwvm_feature_flags(),"--runtime-"+engine,"--debug-fault-action","exit",
                     "--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable","--run",guest])
    if args.probe_legacy_abi:
        from herbceptions_sysroot import verify_exception_bridge
        report["scope"] = "Portable domains and the stable libc++abi translation unit against a baseline sysroot"
        verify_exception_bridge(sysroot,triple,tc,False)
        tree = source.parent
        cxa = tree/"libcxxabi/src/itanium_exception_ptr.cpp"
        report["cxxabi_source"] = {p.name:digest(p) for p in [cxa,cxa.with_suffix(".h")]}
        obj, guest = out/"exception-domain.o", out/"legacy.wasm"
        args_cpp = ["-O3","-g","-std=c++23","-D_HERBCEPTIONS_BUILDING_RUNTIME=1",
                    *["-I"+str(tree/path) for path in ("libherbceptions/include","libherbceptions/src",
                                                        "libcxxabi/src","libcxxabi/include","libunwind/include")],
                    "-c",str(cxa),"-o",str(obj)]
        cmd,_ = make_command(tc,[args.sysroots],profile,"cpp",args_cpp,verify=True)
        run("compile-legacy-domain",cmd)
        cmd,_ = make_command(tc,[args.sysroots],profile,"cpp",["-O3","-g","-std=c++20","-mexec-model=reactor",
            "-Wl,--no-entry,--export=_start",str(HERE/"legacy_domain.cpp"),str(obj),"-o",str(guest)],verify=True)
        run("link-legacy-domain", cmd, None if args.eh else b"undefined symbol: __cxa_error_domain_itanium_exception_ptr")
        if args.eh:
            if inspect(guest.read_bytes()):
                raise ValueError("exception bridge unexpectedly imports host capabilities")
            report["legacy_wasm_sha256"] = digest(guest)
            for engine in ("int","aot"):
                run("legacy-"+engine,[args.vm.resolve(),*profile.uwvm_feature_flags(),"--runtime-"+engine,
                    "--debug-fault-action","exit","--runtime-compile-threads","0","--runtime-llvm-jit-cache-path","disable",
                    "--run",guest])
    report["complete"]=True;save()


if __name__ == "__main__":
    main()
