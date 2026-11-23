"""Rebuild the CPython target archive from the editable release and link the shared guest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from link import CONFIG, LIBDIR, PRODUCER, SHARED, backend, link, preopen_source_hashes
import wasip1

BUILTINS = {"math", "array", "_struct", "binascii", "_json", "cmath", "_heapq", "_bisect",
            "_random", "_statistics", "_contextvars"}


def cold_archive(sdk, work, jobs, cc_sdk=None):
    """Build the matching native freezer and target libpython with the installed WasmMTE compiler."""
    cc, producer, tools, env = backend(sdk, cc_sdk)
    source = work / "Python-3.14.8"
    shutil.copytree(sdk / "src/runtimes/cpython/upstream", source)
    native, target = work / "native", work / "target"
    native.mkdir()
    (target / "Modules").mkdir(parents=True)
    env.update(TMPDIR=str(work), SOURCE_DATE_EPOCH="1790812800", PYTHONDONTWRITEBYTECODE="1")
    host = dict(env, PATH="/usr/bin:/bin", CC="/usr/bin/cc", AR="/usr/bin/ar",
                RANLIB="/usr/bin/ranlib", CFLAGS="-O2")
    configure = ["/bin/sh", source / "configure", "--without-ensurepip", "--disable-test-modules"]
    subprocess.run(configure, cwd=native, env=host, check=True)
    subprocess.run(["make", f"-j{jobs}", "python"], cwd=native, env=host, check=True)
    freezer = native / "python"
    modules = re.findall(r"^@MODULE_\w+_TRUE@(\w+) ", (source / "Modules/Setup.stdlib.in").read_text(), re.M)
    if not {"_socket", "_ctypes"} <= set(modules):
        raise ValueError("unexpected upstream extension inventory")
    (target / "Modules/Setup.local").write_text("*disabled*\n" + "\n".join(sorted(set(modules) - BUILTINS)) + "\n")
    flags = ["-O3", "-g", "-DUWROS_WASM_MTE=1", f"-ffile-prefix-map={sdk}=/wros/sdk",
             f"-ffile-prefix-map={work}=/wros/build", f"-ffile-prefix-map={tools}=/wros/toolchain",
             "-fdebug-compilation-dir=/wros/build"]
    for option, logical in (("--sysroot=", "/wros/sysroot"), ("-resource-dir=", "/wros/resource")):
        actual = next(arg[len(option):] for arg in cc if arg.startswith(option))
        flags.append(f"-ffile-prefix-map={actual}={logical}")
    guest = dict(env, CC=shlex.join(cc), AR=str(tools / "bin/llvm-ar"),
                 RANLIB=shlex.join([str(tools / "bin/llvm-ar"), "s"]), READELF="/usr/bin/readelf",
                 CONFIG_SITE=str(source / "Tools/wasm/wasi/config.site-wasm32-wasi"),
                 PKG_CONFIG_LIBDIR="/nonexistent", CFLAGS=shlex.join(flags), ac_cv_func_dlopen="no",
                 LDFLAGS="-Wl,-z,stack-size=8388608 -Wl,--max-memory=268435456 -Wl,--threads=1")
    machine = subprocess.check_output(["/usr/bin/cc", "-dumpmachine"], env=host, text=True).strip()
    subprocess.run([*configure, "--host=wasm32-unknown-wasip1", "--build=" + machine,
                    "--with-build-python=" + str(freezer), "--disable-wasm-pthreads", "--without-pymalloc",
                    "--without-mimalloc", "--prefix=/wros/python"], cwd=target, env=guest, check=True)
    subprocess.run(["make", f"-j{jobs}", "-f", "Makefile", "-f", HERE / "runtime_paths.mk",
                    "UWVM_PYTHON_LOGICAL_SOURCE=/wros/python", "libpython3.14.a"], cwd=target, env=guest, check=True)
    subprocess.run([freezer, "-I", "-B", HERE / "freeze_encodings.py", "--source", source,
                    "--out", target / "frozen.h"], cwd=target, env=host, check=True)
    products = {}
    for name in ("libpython3.14.a", "pyconfig.h", "frozen.h"):
        out = sdk / (LIBDIR if name.endswith(".a") else CONFIG) / name
        out.parent.mkdir(parents=True, exist_ok=True)
        products[name] = hashlib.sha256((target / name).read_bytes()).hexdigest()
        # Replace each staged inode. Installer inputs may be hard-linked to its immutable cache.
        os.replace(target / name, out)
    snapshot = (sdk / "src/runtimes/cpython/upstream.sha256").read_bytes()
    receipt = {"source_index_sha256": hashlib.sha256(snapshot).hexdigest(),
               "compiler_sha256": producer["compiler_sha256"], "closure_sha256": producer["closure_sha256"],
               "profile": producer["profile"], "extracted": products}
    pending = work / "producer.json"
    pending.write_text(json.dumps(receipt, indent=2) + "\n")
    (sdk / PRODUCER).parent.mkdir(parents=True, exist_ok=True)
    os.replace(pending, sdk / PRODUCER)


def check_shared(sdk, cc_sdk, directory):
    """Inspect the release bytes and distinguish the historical module from a relink."""
    sys.path.insert(0, str((cc_sdk or sdk / "libexec/cpython-c") / "install"))
    from guest_profile import Profile
    from imports import inspect
    guest = directory / SHARED.name
    blob = guest.read_bytes()
    record = json.loads(guest.with_suffix(".json").read_bytes())
    digest = hashlib.sha256(blob).hexdigest()
    memories = []
    imports = inspect(blob, memory_types=memories)
    library = json.loads((sdk / PRODUCER).read_bytes())
    if (record["sha256"] != digest or record["bytes"] != len(blob) or record["imports"] != imports or
            record["profile"] != Profile().to_dict() or memories != [32] or
            record["libpython_sha256"] != library["extracted"]["libpython3.14.a"]):
        raise ValueError("shared CPython differs from its module or library receipt")
    names = set()
    for row in imports:
        name = row["name"]
        if (row["module"] != "wasi_snapshot_preview1" or row["kind"] != 0 or
                row["params"] != wasip1.SIGNATURES.get(name) or row["results"] != ([] if name == "proc_exit" else ["i32"])):
            raise ValueError("unexpected shared CPython import: " + name)
        names.add(name)
    sources = record.get("libc_preopen_sources_sha256")
    if sources is None and "fd_readdir" not in names:
        state = "awaiting-relink"
    elif sources == preopen_source_hashes() and wasip1.SHARED_ONLY <= names:
        state = "linked"
    else:
        raise ValueError("shared CPython preopen sources or directory imports differ from this SDK")
    return {"read_only_directory": state, "sha256": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True, help="isolated SDK staging prefix")
    parser.add_argument("--cc-sdk", type=Path, help="standalone verified C SDK, default SDK/libexec/cpython-c")
    parser.add_argument("--work", type=Path, help="private build directory")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-source", action="store_true", help="build libpython and config headers in --sdk before linking")
    mode.add_argument("--check-shared", type=Path, metavar="DIR", help="verify a shared Wasm and JSON receipt and report link status")
    parser.add_argument("--output-dir", type=Path, help="publish the shared Wasm and receipt to a new directory")
    parser.add_argument("--jobs", type=int, default=2)
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error("--jobs must be positive")
    sdk = opts.sdk.resolve()
    cc_sdk = opts.cc_sdk.resolve() if opts.cc_sdk else None
    if opts.check_shared:
        if opts.output_dir:
            parser.error("--output-dir is a build option")
        print(json.dumps(check_shared(sdk, cc_sdk, opts.check_shared)))
        return
    if opts.work is None:
        parser.error("--work is required for a build")
    opts.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=opts.work.resolve(), prefix="cpython-") as scratch:
        work = Path(scratch)
        if opts.from_source:
            cold_archive(sdk, work, opts.jobs, cc_sdk)
        destination = opts.output_dir.resolve() if opts.output_dir else (sdk / SHARED).parent
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".cpython-") as staging:
            release = Path(staging) / "release"
            guest = release / SHARED.name
            record = link(sdk, guest, "generic", cc_sdk=cc_sdk)
            receipt = guest.with_suffix(".json")
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            if opts.output_dir or not destination.exists():
                release.rename(destination)
            else:
                os.replace(guest, destination / guest.name)
                os.replace(receipt, destination / receipt.name)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit("CPython build failed: " + str(error))
