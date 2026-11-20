#!/usr/bin/env python3
"""Build and test an official Zend Embed SAPI as a sealed Core Wasm guest."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import suppress
import hashlib
import io
import json
import os
import re
import resource
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(SDK / "tests"))
sys.path.insert(0, str(SDK / "install"))

from compiler import compiler_environment, digest, make_command
from frontend import audit
from guest_profile import Profile
from imports import inspect
from separate_compilation import cgroup_record


PHP_RELEASE = "8.6.0"
PHP_SOURCE_BYTES = 15148068
PHP_SOURCE_SHA256 = "5f84beaa3d763aee1e4feed99bf54ec692c383b322e25626807b589238c3a087"
EMULATION = ["signal", "process-clocks", "getpid", "mman"]
CLOCK_ENV_IMPORTS = {"environ_get", "environ_sizes_get", "clock_time_get", "proc_exit"}
DENIED_WASI = (
    "fd_close", "fd_datasync", "fd_fdstat_get", "fd_fdstat_set_flags", "fd_filestat_get",
    "fd_filestat_set_size", "fd_pread", "fd_prestat_dir_name", "fd_prestat_get", "fd_read",
    "fd_readdir", "fd_seek", "fd_sync", "fd_tell", "fd_write", "path_create_directory",
    "path_filestat_get", "path_filestat_set_times", "path_link", "path_open", "path_readlink",
    "path_remove_directory", "path_rename", "path_symlink", "path_unlink_file", "poll_oneoff",
)


def replace_once(file: Path, anchor: str, replacement: str) -> None:
    text = file.read_text()
    if text.count(anchor) != 1:
        raise ValueError(f"unexpected source anchor in {file.name}")
    file.write_text(text.replace(anchor, replacement, 1))


def source_snapshot(path: Path, name: str, extent: int, sha256: str) -> io.BytesIO:
    """Read exactly the pinned archive and extract from the bytes that passed verification."""
    if not path.is_file():
        raise ValueError(f"{name} source must be a regular archive file: {path}")
    with path.open("rb") as source:
        data = source.read(extent + 1)
    if len(data) != extent or hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"{name} source archive differs from the pinned release: {path}")
    return io.BytesIO(data)


def prepare_sources(work: Path, php_archive: Path, wasi_archive: Path,
                    mte: bool, report: dict) -> tuple[Path, Path, Path]:
    """Extract verified upstream inputs and apply the guest-only SAPI restrictions."""
    lock = json.loads((SDK / "tools/wasm/memtag/source-lock.json").read_bytes())
    wasi = lock["sources"]["wasi-libc-sdk34"]
    php_input = source_snapshot(php_archive, f"PHP {PHP_RELEASE}", PHP_SOURCE_BYTES, PHP_SOURCE_SHA256)
    wasi_input = source_snapshot(wasi_archive, "wasi-libc SDK 34",
                                 wasi["archive_bytes"], wasi["archive_sha256"])
    report.update(php_archive_sha256=PHP_SOURCE_SHA256, wasi_libc_archive_sha256=wasi["archive_sha256"])
    with php_input, tarfile.open(fileobj=php_input, mode="r:xz") as stream:
        stream.extractall(work, members=(member for member in stream if not member.name.endswith(".phpt")),
                          filter="data")

    source = work / f"php-{PHP_RELEASE}"
    replace_once(
        source / "Zend/zend_portability.h",
        "#ifndef ZEND_WIN32\n# define SETJMP(a) sigsetjmp(a, 0)",
        "#if !defined(ZEND_WIN32) && !defined(__wasi__)\n# define SETJMP(a) sigsetjmp(a, 0)",
    )
    if mte:
        # Zend already supplies a heap implementation of this API. Select it
        # for variable-sized scratch allocations with no statically known extent.
        replace_once(
            source / "Zend/zend_portability.h",
            "#if !ZEND_DEBUG && (defined(HAVE_ALLOCA)",
            "#if !defined(__wasi__) && !ZEND_DEBUG && (defined(HAVE_ALLOCA)",
        )
    replace_once(
        source / "sapi/embed/php_embed.c",
        "static const char HARDCODED_INI[] =\n",
        "static const char HARDCODED_INI[] =\n"
        '    "opcache.enable=0\\n"\n'
        '    "opcache.enable_cli=0\\n"\n'
        '    "enable_dl=0\\n"\n'
        '    "allow_url_fopen=0\\n"\n'
        '    "allow_url_include=0\\n"\n',
    )
    overlay = work / "include"
    (overlay / "sys").mkdir(parents=True)
    for name in ("wros_posix.h", "ucontext.h", "sys/un.h", "sys/wait.h"):
        shutil.copyfile(HERE / name, overlay / name)
    runtime = work / "sjlj.c"
    prefix = wasi["root"] + "/libc-top-half/musl/"
    inputs = {"src/setjmp/wasm32/rt.c": runtime,
              **{f"include/{name}": overlay / name for name in ("netdb.h", "pwd.h", "grp.h", "syslog.h")}}
    with wasi_input, tarfile.open(fileobj=wasi_input, mode="r:xz") as stream:
        for relative, destination in inputs.items():
            member = stream.getmember(prefix + relative)
            if not member.isfile():
                raise ValueError(f"unexpected wasi-libc source member {relative}")
            with stream.extractfile(member) as source_file, destination.open("xb") as target:
                shutil.copyfileobj(source_file, target)
    report["sjlj_source_sha256"] = digest(runtime)
    return source, overlay, runtime


def write_denials(header: Path, output: Path) -> list[str]:
    """Generate link-time refusals with the exact selected libc signatures."""
    source = re.sub(r"/\*.*?\*/", "", header.read_text(), flags=re.S)
    signatures = dict(re.findall(
        r"\b__wasi_errno_t\s+(__wasi_\w+)\s*(\([^()]*\))\s*__attribute__", source
    ))
    missing = sorted(name for name in DENIED_WASI if "__wasi_" + name not in signatures)
    if missing:
        raise ValueError(f"{header.name} lacks expected WASI declarations for {', '.join(missing)}")
    stubs = ["#include <wasi/api.h>", ""]
    wrappers = []
    for operation in DENIED_WASI:
        name = "__wasi_" + operation
        args = " ".join(signatures[name].split())
        # libc stops preopen enumeration at BADF. No descriptor is preopened.
        error = "BADF" if operation == "fd_prestat_get" else "NOTCAPABLE"
        stubs.append(f"__wasi_errno_t __wrap_{name}{args} {{ return __WASI_ERRNO_{error}; }}")
        wrappers.append(f"-Wl,--wrap={name}")
    output.write_text("\n".join(stubs) + "\n")
    return wrappers


def logged(argv: list[str | Path], cwd: Path, env: dict, log: Path, limit: int) -> None:
    with log.open("wb") as stream:
        result = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        try:
            status = result.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(result.pid, signal.SIGKILL)
            result.wait()
            raise
    if status:
        output = log.read_text(errors="replace")
        errors = [line for line in output.splitlines() if "error:" in line][:4]
        diagnostic = "\n".join(errors) if errors else output[-3200:].strip()
        raise RuntimeError(f"{log.name} exit {status}\n{diagnostic}")


def check_tag_operations(opts: argparse.Namespace, artifact: Path, env: dict, report: dict) -> None:
    """Count decoded managed-owner instructions, if the producer built that profile."""
    if not opts.mte:
        return
    disassembly = subprocess.run(
        [opts.toolchain / "bin/llvm-objdump", "-d", "--mattr=+memtag", artifact],
        env=env, stdout=subprocess.PIPE, timeout=60, check=True,
    )
    owner = re.compile(rb"\bmemtag\.(claimz?|reserve|activate|release)\s+\d+")
    counts = Counter(match[1].decode("ascii") for match in owner.finditer(disassembly.stdout))
    if not (counts["claim"] + counts["claimz"]) or not counts["release"]:
        raise ValueError("requested MTE module lacks decoded allocation and release operations")
    report["managed_owner_instructions"] = dict(counts)


def build(opts: argparse.Namespace, work: Path, report: dict) -> Path:
    profile = Profile(32, "3.0", False, opts.mte, "eh")
    manifest = json.loads(opts.sysroots.read_bytes())
    policy = manifest.get("producer_allocation_policy")
    if opts.mte and policy != "managed-neighborhood":
        raise ValueError("use the managed-neighborhood compiler and matching sysroot for the MTE probe")
    cc, closure = make_command(opts.toolchain, [opts.sysroots], profile, "c", ["-c"], verify=True)
    report.update(sdk_c_closure=closure, producer_allocation_policy=policy)
    cc = cc[:-1] + ["-mllvm", "-wasm-enable-sjlj"]
    source, overlay, runtime = prepare_sources(work, opts.php_source, opts.wasi_source, opts.mte, report)
    report["stage"] = "configuring"
    target = work / "target"
    target.mkdir()
    staging = work / "transient"
    staging.mkdir()
    env = dict(compiler_environment(opts.toolchain), TMPDIR=str(staging))
    flags = ["-O3", "-gline-tables-only", "-I" + str(overlay),
             "-ffile-prefix-map=" + str(work) + "=/wros/php",
             "-fdebug-compilation-dir=/wros/php",
             *("-D_WASI_EMULATED_" + name.upper().replace("-", "_") for name in EMULATION)]
    link = ["-Wl,-z,stack-size=2097152", "-Wl,--max-memory=268435456", "-Wl,--threads=1"]
    system = ["-l" + "wasi-emulated-" + name for name in EMULATION]
    runtime_object = target / "wasm_sjlj.o"
    logs = opts.output
    logged([*cc, *flags, "-c", runtime, "-o", runtime_object], target, env, logs / "sjlj.log", 60)

    configure_env = dict(env, CC=shlex.join(cc), CFLAGS=shlex.join(flags),
                        AR=str(opts.toolchain / "bin/llvm-ar"), RANLIB=str(opts.toolchain / "bin/llvm-ranlib"),
                        LIBS=shlex.join([str(runtime_object), *system, "-lunwind"]),
                        LDFLAGS=shlex.join(link), PKG_CONFIG_LIBDIR="/nonexistent")
    build_host = subprocess.check_output(["/usr/bin/cc", "-dumpmachine"], env=env, text=True).strip()
    logged(["/bin/sh", source / "configure", "--host=wasm32-unknown-wasip1", "--build=" + build_host,
            "--disable-all", "--enable-embed=static", "--disable-cgi", "--disable-phpdbg",
            "--disable-zend-signals", "--disable-opcache-jit", "--disable-huge-code-pages",
            "--without-pcre-jit", "--without-pear", "--disable-phar", "--without-iconv", "--without-valgrind"],
           target, configure_env, logs / "configure.log", 200)
    config = target / "main/php_config.h"
    if "#define HAVE_GETRUSAGE 1" in config.read_text():
        replace_once(config, "#define HAVE_GETRUSAGE 1", "/* #undef HAVE_GETRUSAGE */")
    # Configure probes only need the upstream system headers. The actual static
    # archive additionally uses our guest-local declarations for denied APIs.
    report["stage"] = "building-zend"
    logged(["/usr/bin/make", "-j4", "EXTRA_LIBS=", "ZEND_EXTRA_LIBS=",
            "EXTRA_CFLAGS=-include " + shlex.quote(str(overlay / "wros_posix.h")), "libphp.la"],
           target, configure_env, logs / "compile.log", 420)

    guest = next(row for row in manifest["targets"] if row["guest_profile"] == profile.to_dict())
    wasi_header = opts.sysroots.parent / guest["sysroot"] / "include/wasm32-wasip1/wasi/wasip1.h"
    deny = work / "deny_wasi.c"
    wrappers = write_denials(wasi_header, deny)
    archive = target / ".libs/libphp.a"
    output = work / "php.wasm"
    includes = [str(root / folder) for root in (target, source)
                for folder in ("", "main", "Zend", "TSRM", "sapi/embed")]
    logged([*cc, *flags, "-D_GNU_SOURCE", "-include", overlay / "wros_posix.h",
            *("-I" + value for value in includes), *wrappers, *link,
            "-nostartfiles", "-Wl,--entry=_start", HERE / "program.c", HERE / "deny_posix.c",
            deny, archive, runtime_object, "-lc-printscan-long-double", *system, "-lunwind", "-o", output],
           target, env, logs / "link.log", 90)
    data = output.read_bytes()
    imports = inspect(data)
    audit(data, profile)
    if {row["name"] for row in imports} != CLOCK_ENV_IMPORTS or any(
            row["module"] != "wasi_snapshot_preview1" for row in imports):
        raise ValueError("unexpected PHP smoke imports")
    check_tag_operations(opts, output, env, report)
    published = opts.output / output.name
    output.replace(published)
    report.update(imports=imports, wasm_sha256=digest(published), bytes=len(data),
                  stage="compiled-and-audited")
    return published


def execute(opts: argparse.Namespace, artifact: Path, report: dict) -> None:
    engine_profile = Profile(32, "3.0", False, opts.mte, "eh")
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TZ": "UTC", "TMPDIR": str(artifact.parent),
           "WROS_PHP_HOST_ONLY": "sentinel"}
    for requested in (True, False) if opts.mte else (False,):
        for engine in ("int", "aot"):
            base = [opts.vm, *engine_profile.uwvm_feature_flags(), "--wasm-set-main-module-name", "main",
                    "--runtime-" + engine, "--runtime-compile-threads", "0",
                    "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit",
                    "--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                    "--wasip1-single-noinherit-system-environment", "main"]
            tag_flags = ["--runtime-memtag-mode", "sync"] if requested else ["--runtime-disable-memtag"]
            for row in report["imports"]:
                name = row["name"]
                base += ["--wasip1-single-interface", "main", name, "deny" if name == "proc_exit" else "allow"]
            for grant in ("environ", "realtime-clock", "monotonic-clock"):
                base += ["--wasip1-single-grant", "main", grant]
            if engine == "aot":
                base += ["--runtime-llvm-jit-policy", "fast-compile"]
            label = engine + ("-sync" if requested else "-off")
            logged([*base, *tag_flags, "--run", artifact], opts.output, env, opts.output / f"{label}.log", 200)
            report["passed_engines"].append(label)
            print(f"PHP {PHP_RELEASE} {label} passed", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("php-source", "wasi-source", "toolchain", "sysroots", "output", "vm"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    opts = parser.parse_args()
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if ".tmp" not in opts.output.parts:
        raise ValueError("put the PHP test output in a new .tmp directory")
    opts.output.mkdir(mode=0o700)
    report = {"php_version": PHP_RELEASE, "guest": "Core 3.0 wasm32 single-threaded EH",
              "debug_info": "DWARF line tables", "mte_requested": opts.mte,
              "cgroup": group, "passed_engines": [], "stage": "checking-inputs",
              "complete": False}
    try:
        if not opts.vm.is_file() or not os.access(opts.vm, os.X_OK):
            raise ValueError(f"the VM must be a regular executable file: {opts.vm}")
        if not opts.sysroots.is_file():
            raise ValueError(f"the sysroot receipt must be a regular file: {opts.sysroots}")
        report["vm_sha256"] = digest(opts.vm)
        with tempfile.TemporaryDirectory(dir=opts.output) as scratch:
            artifact = build(opts, Path(scratch), report)
        execute(opts, artifact, report)
        report.update(stage="executed", complete=True)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as error:
        report["failure"] = str(error)
        print(f"PHP {PHP_RELEASE} {report['stage']}: {error}", file=sys.stderr)
        return 1
    finally:
        (opts.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
