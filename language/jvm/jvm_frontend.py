#!/usr/bin/env python3
"""Compile an experimental closed Java or Kotlin entry to a wasm32 ROS module."""
import argparse
import hashlib
import json
import os
import re
import tempfile
import subprocess
import sys
from pathlib import Path
from operations import render

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def compile_guest(opts, language, work):
    sdk=HERE.parents[1]
    vendor=sdk/"third-parties/jvm"
    sources=opts.sources
    sys.path.insert(0,str(sdk/"install"))
    from artifacts import read_bounded
    from private_exports import keep_private_memory
    from compiler import compiler_environment, make_command
    from frontend import audit
    from imports import inspect
    from guest_profile import Profile

    for name in ("tmp", "host", "app", "runtime", "generated"):
        (work / name).mkdir()
    bridge, methods = render(sdk/"share/abi/ros.json", opts.ros_operation, work)
    host = opts.bundle.resolve()
    host_manifest=HERE.parent / language / "host-inputs.json"
    manifest=json.loads(host_manifest.read_text())
    jars = []
    for row in manifest["files"]:
        path = host / row["path"]
        if not path.resolve().is_relative_to(host) or sha(path) != row["sha256"]:
            raise ValueError("host payload differs from the pinned source manifest")
        if row["path"].startswith("compiler-jars/"):
            jars.append(str(path))
    cp = os.pathsep.join(sorted(jars))
    java = [host / "jdk21/bin/java", "-Xint", "-XX:-CreateCoredumpOnCrash", "-XX:ActiveProcessorCount=1", "-Xms48m", "-Xmx768m",
            "-Djava.io.tmpdir=" + str(work/"tmp")]
    env = dict(PATH=os.defpath, HOME=str(work/"tmp"), TMPDIR=str(work/"tmp"), LC_ALL="C.UTF-8", TZ="UTC")
    env["LD_LIBRARY_PATH"] = os.pathsep.join(str(host / part) for part in ("lib/host-runtime", "jdk21/lib/server", "jdk21/lib"))
    s = HERE
    log = []
    def run(name, argv, environ=env):
        result = subprocess.run(argv, cwd=work, env=environ, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=240)
        (work / (name + ".log")).write_bytes(result.stdout)
        log.append(dict(name=name, argv=list(map(str,argv)), exit=result.returncode))
        if result.returncode:
            raise RuntimeError(f"{name} failed; {result.stdout.decode(errors='replace')[-1800:]}")
    javac = java + ["-m", "jdk.compiler/com.sun.tools.javac.Main", "-proc:none", "-g"]
    run("host-translator", javac + ["-cp", cp, "-d", work/"host", s/"Translate.java", s/"Admit.java",
        vendor/"java/org/teavm/backend/c/CTarget.java", vendor/"java/org/teavm/backend/c/generate/ClassGenerator.java"])
    run("guest-runtime", javac + ["-cp",cp,"-d",work/"runtime",vendor/"java/org/teavm/runtime/GC.java",
        vendor/"java/org/teavm/runtime/Allocator.java",s/"java/wros/scene/MessageFrame.java",*bridge,s/"java/wros/scene/Driver.java",s/"java/wros/scene/Guard.java", s/"java/wros/scene/Scene.java"])
    app_cp = str(work/"runtime") + ":" + cp
    if language == "java":
        run("application", javac + ["--source","21","--target","21","-cp",app_cp,"-d",work/"app",*sources])
    else:
        run("application", java + ["-cp",cp,"org.jetbrains.kotlin.cli.jvm.K2JVMCompiler",
            "-jvm-target","17","-no-stdlib","-no-reflect","-classpath",app_cp,"-d",work/"app",*sources])
    run("check-bytecode",java+["-cp",str(work/"host")+":"+cp,"Admit",work/"app",opts.main_class,*methods])
    input_cp = str(work/"runtime") + ":" + str(work/"app") + ":" + cp
    host_cp = str(vendor/"resources") + ":" + str(work/"host") + ":" + input_cp
    run("aot", java + ["-cp",host_cp,"Translate","C",work/"generated",input_cp,opts.main_class])
    result = work / "application.wasm"
    toolchain = opts.toolchain.resolve()
    argv, identity = make_command(toolchain, [opts.sysroots.resolve()], Profile(), "c", [
        "-O3","-g","-std=gnu11","-ffunction-sections","-fdata-sections",
        "-Wno-incompatible-pointer-types","-Wno-return-type","-Wno-deprecated-non-prototype",
        str(s/"guest.c"),"-iquote",str(work/"generated"),"-D__WASM_MEMTAG__=1",
        "-include",str(s/"contracts.h"),"-I"+str(sdk/"include"),"-include","wros/scene.h","-nostartfiles",
        "-Wl,--stack-first,-z,stack-size=131072,--max-memory=268435456,--no-entry,--export=_start",
        "-o", str(result)], verify=True)
    run("wasm",argv, dict(compiler_environment(toolchain),TMPDIR=str(work/"tmp")))
    linked = read_bounded(result)
    guest = keep_private_memory(linked, {"_start"}, max_pages=4096)
    result.write_bytes(guest)
    audit(guest,Profile())
    supported = {("uwvm_ros_v2", n) for n in ("abi", "capability.open", "capability.close", "guard.create", "guard.trigger", "guard.take", "driver.connect", "driver.submit", "driver.result", "driver.describe", "driver.disconnect")}
    if opts.ros_operation:
        supported = {("uwvm_ros_v2", name) for name in opts.ros_operation}
    supported.add(("wasi_snapshot_preview1", "clock_time_get"))
    if any((i["module"], i["name"]) not in supported for i in inspect(guest)):
        raise ValueError("unexpected host import for the synchronous JVM profile")
    receipt={"profile":"synchronous-aot","import_surface":inspect(guest),"compiler_identity":identity,"guest_sha256":sha(result),
             "linked_sha256":hashlib.sha256(linked).hexdigest(),"steps":log,"sources":{str(f):sha(f) for f in sources},"host_manifest_sha256":sha(host_manifest)}
    if opts.work:
        (work/"results.json").write_text(json.dumps(receipt,indent=2)+"\n")
    with tempfile.NamedTemporaryFile(dir=opts.output.parent,suffix=".wasm",delete=False) as temp:
        pending=Path(temp.name)
        try:
            temp.write(guest)
            temp.flush()
            os.fsync(temp.fileno())
            os.replace(pending,opts.output)
        finally:
            pending.unlink(missing_ok=True)
    return 0

def main(language):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain","sysroots","bundle"):
        parser.add_argument("--"+name,type=Path)
    parser.add_argument("--work",type=Path,help="keep compiler logs in a new directory")
    parser.add_argument("--main-class",required=True)
    parser.add_argument("--ros-operation",action="append",default=[],help="admit precisely this ROS op and generate its Calls method; repeat for more")
    parser.add_argument("-o","--output",required=True,type=Path)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--mte",action="store_true")
    mode.add_argument("--no-mte",action="store_true")
    mode.add_argument("--legacy-mte",action="store_true")
    parser.add_argument("sources",nargs="+",type=Path)
    opts=parser.parse_args()
    if opts.no_mte:
        parser.error("no signed strict or MTE-off release is available for the uninstrumented JVM profile")
    if opts.legacy_mte and not all((opts.toolchain, opts.sysroots, opts.bundle)):
        parser.error("--legacy-mte requires explicit --toolchain, --sysroots and --bundle")
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z_$0-9]*(?:\.[A-Za-z_$][A-Za-z_$0-9]*)*",opts.main_class):
        parser.error("invalid JVM class name")
    if opts.output.suffix!=".wasm" or not opts.output.parent.is_dir():
        parser.error("expected a .wasm output with an existing parent")
    suffix=".java" if language=="java" else ".kt"
    try:
        if not opts.legacy_mte:
            from release import authorize, local_release
            _, tc, sysroot, host = authorize(local_release.site_config(HERE.parents[1]), language)
            for name, selected in (("toolchain", tc), ("sysroots", sysroot), ("bundle", host)):
                supplied = getattr(opts, name)
                if supplied is not None and supplied.resolve(strict=True) != selected:
                    raise ValueError("explicit " + name + " differs from the signed JVM site")
                setattr(opts, name, selected)
        opts.sources=[p.resolve(strict=True) for p in opts.sources]
        if len(opts.sources) > 256 or any(
                not p.is_file() or p.suffix != suffix or p.stat().st_size > 16 * 1024 * 1024
                for p in opts.sources):
            raise ValueError("expected bounded source files for the selected language")
        if opts.legacy_mte:
            print("warning: explicitly selected unsigned synchronous JVM AOT with WasmMTE instrumentation",file=sys.stderr)
        if opts.work:
            work=opts.work.resolve()
            work.mkdir(exist_ok=False)
            return compile_guest(opts,language,work)
        with tempfile.TemporaryDirectory(prefix=".wros-jvm-",dir=opts.output.parent) as tmp:
            return compile_guest(opts,language,Path(tmp).resolve())
    except (OSError,KeyError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        parser.exit(1,f"{parser.prog}: {error}\n")
