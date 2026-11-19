"""@file build_interpreter.py
@brief Build guest CPython from the verified Python.org source using the selected WROS C compiler.
"""
import hashlib
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
LANG = ROOT / "language/py"
VERSION = "3.14.8"
ARCHIVE = ROOT / "third-parties/cpython" / ("Python-" + VERSION + ".tar.xz")
SHA256 = "c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73"
BUILTINS = {"math", "array", "_struct", "binascii", "_json", "cmath", "_heapq", "_bisect",
            "_random", "_statistics", "_contextvars"}
LINK_LIBRARIES = ["-lwasi-emulated-getpid", "-lwasi-emulated-signal", "-lwasi-emulated-process-clocks",
                  "-lc-printscan-long-double", "-lm"]


def prepare_source(output, profile):
    """@brief Authenticate one official source archive and apply reviewed embedding changes.

    @param output Private build directory. The extracted source stays outside the installed SDK.
    @param profile Verified core Wasm ABI and MTE selection.
    @return A private source tree restricted to the configured static interpreter.
    """
    with ARCHIVE.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != SHA256:
            raise ValueError("unexpected CPython source archive")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:xz") as archive:
            archive.extractall(output, filter="data")
    source = output / ("Python-" + VERSION)
    if profile.mte:
        header = source / "Include/internal/pycore_freelist.h"
        before = header.read_text()
        old = "    if (fl->size < maxsize && fl->size >= 0) {"
        if before.count(old) != 1:
            raise ValueError("CPython object-freelist implementation differs from the reviewed source")
        start = before.index(old)
        end = before.index("\n}", start)
        header.write_text(before[:start] + """    /* Release transient objects through the tagged allocator. */
    (void)fl; (void)obj; (void)maxsize;
    return 0;""" + before[end:])
    return source


def build(work, profile, cc, env, toolchain, jobs):
    """@brief Compile the native bytecode freezer and the guest interpreter from one authenticated release.

    @param work Private output directory on a filesystem which permits build tools to execute.
    @param profile Exact guest ABI. The single-threaded interpreter uses libc for every object allocation.
    @param cc Reviewed compiler command resolved by the SDK.
    @param env Sanitized compiler environment.
    @param toolchain Selected target tools.
    @param jobs Maximum parallel make jobs for this build.
    @return Guest archive, upstream headers, build headers, and frozen encoding definitions.
    """
    env = dict(env, SOURCE_DATE_EPOCH="1790812800")
    source = prepare_source(work, profile)
    native, target = work / "native", work / "target"
    native.mkdir()
    (target / "Modules").mkdir(parents=True)
    def run(argv, cwd, environment):
        log = cwd / "build.log"
        with log.open("ab") as stream:
            proc = subprocess.run(argv, cwd=cwd, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        if proc.returncode:
            with log.open("rb") as stream:
                stream.seek(max(0, log.stat().st_size - 4096))
                raise ValueError("CPython build failed:\n" + stream.read().decode(errors="replace"))
    # Host Python is a build-time tool and cannot run application input.
    native_env = dict(env, PATH="/usr/bin:/bin", CC="/usr/bin/cc", AR="/usr/bin/ar",
                      RANLIB="/usr/bin/ranlib", CFLAGS="-O2")
    configure = ["/bin/sh", source / "configure", "--without-ensurepip", "--disable-test-modules"]
    run(configure, native, native_env)
    run(["/usr/bin/make", "-j" + str(jobs), "python"], native, native_env)
    freezer = native / "python"
    # Disable optional native extensions individually, keeping built-in importlib,
    # encodings, math and container semantics without a filesystem or network.
    optional = re.findall(r"^@MODULE_\w+_TRUE@(\w+) ", (source / "Modules/Setup.stdlib.in").read_text(), re.M)
    if "_socket" not in optional or "_ctypes" not in optional:
        raise ValueError("unexpected CPython extension inventory")
    disabled = sorted(set(optional) - BUILTINS)
    (target / "Modules/Setup.local").write_text("*disabled*\n" + "\n".join(disabled) + "\n")
    flags = ["-O3", "-g", "-ffile-prefix-map=" + str(work) + "=/wros/build",
             "-ffile-prefix-map=" + str(toolchain) + "=/wros/toolchain", "-fdebug-compilation-dir=/wros/build"]
    for option, logical in (("--sysroot=", "/wros/sysroot"), ("-resource-dir=", "/wros/resource")):
        actual = next(arg[len(option):] for arg in cc if arg.startswith(option))
        flags.append("-ffile-prefix-map=" + actual + "=" + logical)
    setup = dict(env, CC=shlex.join(cc), AR=str(toolchain / "bin/llvm-ar"),
                 RANLIB=str(toolchain / "bin/llvm-ranlib"), READELF="/usr/bin/readelf",
                 CONFIG_SITE=str(source / "Tools/wasm/wasi/config.site-wasm32-wasi"),
                 PKG_CONFIG_LIBDIR="/nonexistent", CFLAGS=shlex.join(flags), ac_cv_func_dlopen="no",
                 LDFLAGS="-Wl,-z,stack-size=8388608 -Wl,--max-memory=268435456 -Wl,--threads=1")
    machine = subprocess.check_output(["/usr/bin/cc", "-dumpmachine"], env=native_env, text=True).strip()
    run([*configure, "--host=wasm32-unknown-wasip1", "--build=" + machine,
         "--with-build-python=" + str(freezer), "--disable-wasm-pthreads", "--without-pymalloc",
         "--without-mimalloc", "--prefix=/wros/python"], target, setup)
    run(["/usr/bin/make", "-j" + str(jobs), "-f", "Makefile", "-f", LANG / "runtime_paths.mk",
         "UWVM_PYTHON_LOGICAL_SOURCE=/wros/python", "libpython3.14.a"], target, setup)
    run([freezer, "-I", "-B", LANG / "freeze_encodings.py", "--source", source,
         "--out", target / "frozen.h"], target, native_env)
    return source, target
