"""Link an actual WASI CPython command and check its final permission surface."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
RECIPE_ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import bundle
import wasip1

TRIPLE = "wasm32-wasip1"
FLAVOR = "core3.0-eh-mte"
SHARED = Path("shared") / TRIPLE / FLAVOR / "cpython.wasm"
LIBDIR = Path("lib") / TRIPLE / "cpython3.14"
PRODUCER = Path("share/uwros/cpython") / TRIPLE / "producer.json"
CONFIG = Path("src/runtimes/cpython/config") / TRIPLE
WASI_LIBC = Path("src/compilers/cc/wasi-libc")
PREOPENS = WASI_LIBC / "libc-bottom-half/sources/preopens.c"
LIBC_LOCK = WASI_LIBC / "libc-top-half/musl/src/internal/lock.h"
LIBS = ["-lwasi-emulated-getpid", "-lwasi-emulated-signal", "-lwasi-emulated-process-clocks",
        "-lc-printscan-long-double", "-lm", "-lunwind"]


def preopen_source_hashes():
    return {str(path): hashlib.sha256((RECIPE_ROOT / path).read_bytes()).hexdigest() for path in (PREOPENS, LIBC_LOCK)}


def backend(sdk, cc_sdk=None):
    """Resolve the installed wasm32 compiler and its authenticated library closure."""
    cc_sdk = cc_sdk or sdk / "libexec/cpython-c"
    sys.path.insert(0, str(cc_sdk / "install"))
    from compiler import compiler_environment, make_command
    from guest_profile import Profile
    from portable_cc import prepare
    toolchain, sysroots = prepare(cc_sdk, language="c", triple=TRIPLE)
    command, receipt = make_command(toolchain, [sysroots], Profile(), "c", [], verify=True)
    command.remove("-lunwind")
    return command, receipt, toolchain, compiler_environment(toolchain)


def operations(contract, names):
    registry = {row["name"]: row["wasm_signature"] for row in contract["operations"]}
    selected = {}
    code, table = [], ["static const RawMethod methods[] = {"]
    for name in sorted(set(names)):
        signature = registry.get(name)
        if signature is None or not re.fullmatch(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*", name):
            raise ValueError("unknown ROSv2 operation: " + name)
        params = signature["parameters"]
        if (signature["results"] != ["i32"] or len(params) > 7 or any(t not in {"i32", "i64"} for t in params)):
            raise ValueError("unrepresentable Python ROS import: " + name)
        symbol = name.replace(".", "_")
        declaration = ", ".join("uint" + t[1:] + "_t" for t in params) or "void"
        args = ", ".join(f"(uint{t[1:]}_t)a[{i}]" for i, t in enumerate(params))
        code += [f'__attribute__((import_module("uwvm_ros_v2"), import_name("{name}")))',
                 f"extern uint32_t ros_{symbol}({declaration});",
                 f"static uint32_t call_{symbol}(const uint64_t *a) {{ return ros_{symbol}({args}); }}"]
        mask = sum((t == "i64") << i for i, t in enumerate(params))
        table.append(f'    {{"{name}", {len(params)}, {mask}, call_{symbol}}},')
        selected[name] = signature
    return "\n".join([*code, *table, "    {NULL, 0, 0, NULL}", "};", ""]), selected


def link(sdk, output, platform, *, project=None, entry=None, sources=(), names=(), cc_sdk=None, debug=False):
    """Produce a new guest atomically from the static interpreter and the chosen modules."""
    command, producer, toolchain, env = backend(sdk, cc_sdk)
    from compiler import digest
    from imports import inspect
    runtime = sdk / "src/runtimes/cpython"
    config = sdk / CONFIG
    library = sdk / LIBDIR / "libpython3.14.a"
    lib_receipt = json.loads((sdk / PRODUCER).read_bytes())
    for path in (library, config / "frozen.h", config / "pyconfig.h"):
        if digest(path) != lib_receipt["extracted"][path.name]:
            raise ValueError("CPython release input differs: " + path.name)
    contract_file = sdk / "share/abi/ros.json"
    if not contract_file.is_file():
        contract_file = sdk / "src/abi/contract.json"
    declarations, selected = operations(json.loads(contract_file.read_bytes()), names)
    sysroot = Path(next(word[10:] for word in command if word.startswith("--sysroot=")))
    resource = Path(next(word[14:] for word in command if word.startswith("-resource-dir=")))
    shared = entry is None
    output = output.resolve()
    if output.suffix != ".wasm" or any(output == Path(path).resolve() for path in sources):
        raise ValueError("choose a new .wasm output separate from all Python inputs")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".wrpy-", dir=output.parent) as scratch:
        work = Path(scratch)
        env.update(TMPDIR=str(work), SOURCE_DATE_EPOCH="1790812800")
        bundle.write(sdk, platform, work, project, entry, sources)
        (work / "operations.inc").write_text(declarations)
        denials, wrappers = wasip1.declarations(sysroot / "include" / TRIPLE / "wasi/wasip1.h", shared)
        (work / "permissions.c").write_text(denials)
        artifact = work / "guest.wasm"
        flags = ["-O3", "-DUWROS_WASM_MTE=1", "-fdebug-compilation-dir=/wros/build",
                 f"-ffile-prefix-map={sdk}=/wros/sdk", f"-ffile-prefix-map={sysroot}=/wros/sysroot",
                 f"-ffile-prefix-map={resource}=/wros/resource", f"-ffile-prefix-map={work}=/wros/build"]
        if sdk != RECIPE_ROOT:
            flags.append(f"-ffile-prefix-map={RECIPE_ROOT}=/wros/sdk")
        objects = []
        if shared:
            # Use wasi-libc's preopen registration code from this SDK revision.
            # The published C archive predates its tagged-address bounds check.
            subprocess.run([*command, *flags, "-D__WASM_MEMTAG__=1", "-I" + str((RECIPE_ROOT / LIBC_LOCK).parent),
                            "-c", RECIPE_ROOT / PREOPENS, "-o", "preopens.o"], cwd=work, env=env, check=True)
            objects.append("preopens.o")
        flags += ["-I" + str(config), "-I" + str(runtime / "upstream/Include"), "-I" + str(work)]
        flags += ["-g"] if debug else ["-Wl,--strip-debug"]
        subprocess.run([*command, *flags, HERE / "entry.c", "permissions.c", "sources.S", *objects, library,
                        *wrappers, *LIBS, "-Wl,-z,stack-size=8388608", "-Wl,--max-memory=268435456",
                        "-Wl,--threads=1", "-o", artifact], cwd=work, env=env, check=True)
        data = artifact.read_bytes()
        memories = []
        imports = inspect(data, memory_types=memories)
        if memories != [32]:
            raise ValueError("CPython requires one wasm32 memory")
        actual = set()
        for row in imports:
            name = row["name"]
            if row["module"] == "uwvm_ros_v2" and name in selected:
                signature = selected[name]
                args, returns = signature["parameters"], signature["results"]
                actual.add(name)
            elif row["module"] == "wasi_snapshot_preview1" and name in wasip1.allowed(shared):
                args = wasip1.SIGNATURES[name]
                returns = [] if name == "proc_exit" else ["i32"]
            else:
                raise ValueError(f"unexpected CPython import {row['module']}.{name}")
            if row["kind"] != 0 or row["params"] != args or row["results"] != returns:
                raise ValueError("incompatible CPython core import signature: " + name)
        if actual != selected.keys():
            raise ValueError("linked ROSv2 imports differ from explicit selection")
        if shared:
            wasi = {row["name"] for row in imports if row["module"] == "wasi_snapshot_preview1"}
            missing = wasip1.SHARED_ONLY - wasi
            if missing:
                raise ValueError("shared CPython is missing Preview1 imports: " + ", ".join(sorted(missing)))
        result = {"interpreter": "CPython 3.14.8", "profile": producer["profile"],
                  "link_compiler_sha256": producer["compiler_sha256"], "link_closure_sha256": producer["closure_sha256"],
                  "libpython_sha256": lib_receipt["extracted"][library.name], "sha256": digest(artifact),
                  "bytes": len(data), "imports": imports}
        if shared:
            result["libc_preopen_sources_sha256"] = preopen_source_hashes()
        os.replace(artifact, output)
    return result
