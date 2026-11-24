"""Wasm-only C and C++ compiler driver. Validate imports before publishing output."""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from compiler import make_command
from imports import inspect
import artifacts
import qualification
import optional_isa

ROOT = Path(__file__).resolve().parents[1]


def public_include_dirs(language):
    include = ROOT / "include/u2rosv2"
    directory = "c++" if language == "cpp" else "c"
    directories = [include / "universal" / directory]
    receipt = ROOT / "selection.json"
    if receipt.is_file():
        selection = json.loads(receipt.read_text())
        platform = selection["platform"]
        if selection["language"] != language or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", platform):
            raise ValueError("invalid installed language or platform in selection.json")
        adapter = include / "platform" / platform / directory
        if adapter.is_dir():
            directories.append(adapter)
    return directories


def sysroot_link_flags(names, compile_only):
    """Select guest archives from the receipt-verified library search path."""
    if compile_only and names:
        raise ValueError("-l requires a final link")
    allowed = {"wasi-emulated-getpid", "wasi-emulated-mman", "wasi-emulated-process-clocks",
               "wasi-emulated-signal", "dl", "crypt", "m", "pthread", "resolv", "rt", "util", "xnet",
               "c++experimental", "c-printscan-no-floating-point", "c-printscan-long-double"}
    if any(name not in allowed for name in names):
        raise ValueError("unknown bundled sysroot library")
    formatters = {"c-printscan-no-floating-point", "c-printscan-long-double"}.intersection(names)
    if len(formatters) > 1:
        raise ValueError("select only one libc printf/scanf implementation")
    flags = ["-l" + name for name in names]
    if not compile_only and not formatters:
        flags.append("-lc-printscan-long-double")
    return flags


def shared_memory_link_flags(profile, pages, *, wasi_crt=False):
    """Select a bounded import from the application's own memory-only module."""
    if pages is None:
        return []
    if not profile.threads:
        raise ValueError("--shared-memory-pages requires a thread profile")
    limit = 4096 if profile.address_bits == 32 and profile.mte else 65536
    if type(pages) is not int or not 1 <= pages <= limit:
        raise ValueError(f"--shared-memory-pages must be between 1 and {limit}")
    flags = ["-Wl,--import-memory", f"-Wl,--max-memory={pages * 65536}"]
    if wasi_crt:
        # Preview1 callbacks resolve the command's own memory export. With a
        # shared owner, export the imported memory at the same index.
        if not profile.mte:
            flags.append("-Wl,--export-memory")
        # The host enters this libc function through an export. An application
        # that never calls pthread_create has no relocation to its archive member.
        flags.append("-Wl,--export=wasi_thread_start")
    return flags


def audit(data, profile, shared_memory_pages=None, *, memory64=None):
    """Allow exact ROS signatures and the selected pointer-width Preview1 ABI.

    Preview1 does not standardize memory64: the matching UWVM sysroot uses
    explicit *_wasm64 imports. Neither spelling grants runtime permission.
    """
    abi = json.loads((ROOT / "share/abi/ros.json").read_text())
    approved = {(abi["module"], r["name"]): (r["wasm_signature"]["parameters"], r["wasm_signature"]["results"])
                for r in abi["operations"]}
    suffix = "_wasm64" if profile.address_bits == 64 else ""
    pointer = "i" + str(profile.address_bits)
    for name in ("args_get", "args_sizes_get", "environ_get", "environ_sizes_get"):
        approved["wasi_snapshot_preview1", name + suffix] = ([pointer, pointer], ["i32"])
    approved["wasi_snapshot_preview1", "clock_res_get" + suffix] = (["i32", pointer], ["i32"])
    approved["wasi_snapshot_preview1", "clock_time_get" + suffix] = (["i32", "i64", pointer], ["i32"])
    approved["wasi_snapshot_preview1", "proc_exit" + suffix] = (["i32"], [])
    # libc stdio and the WASIp1 mmap emulation archive reference these exact ABI
    # signatures. The VM independently grants descriptor rights and preopens.
    descriptor_imports = {
        "fd_close": ["i32"],
        "fd_fdstat_get": ["i32", pointer],
        "fd_prestat_get": ["i32", pointer],
        "fd_prestat_dir_name": ["i32", pointer, pointer],
        "fd_read": ["i32", pointer, pointer, pointer],
        "fd_write": ["i32", pointer, pointer, pointer],
        "fd_seek": ["i32", "i64", "i32", pointer],
        "fd_pread": ["i32", pointer, pointer, "i64", pointer],
        "poll_oneoff": [pointer, pointer, pointer, pointer],
    }
    for name, params in descriptor_imports.items():
        approved["wasi_snapshot_preview1", name + suffix] = (params, ["i32"])
    if profile.threads:
        approved["wasi", "thread-spawn"] = (["i32"], ["i32"])
        # libc's pthread scheduler still requires the VM's separate sched-yield grant.
        approved["wasi_snapshot_preview1", "sched_yield" + suffix] = ([], ["i32"])
    shared_memory_link_flags(profile, shared_memory_pages)
    selected_owner = False
    memory_types = []
    allow_memory64 = profile.memory64_enabled(memory64)
    for row in inspect(data, memory_limits=shared_memory_pages is not None, memory_types=memory_types):
        if (shared_memory_pages is not None and not selected_owner and row["kind"] == 2
                and (row["module"], row["name"]) == ("env", "memory")):
            flags, minimum, maximum = row["limits"]
            shared_flags = 7 if profile.address_bits == 64 else 3
            if flags != shared_flags or maximum != shared_memory_pages or not 0 < minimum <= maximum:
                raise ValueError(f"expected a bounded shared wasm{profile.address_bits} env.memory with the selected maximum")
            selected_owner = True
            continue
        expected = approved.get((row["module"], row["name"]))
        if row["kind"] != 0 or expected != (row.get("params"), row.get("results")):
            raise ValueError(f"unauthorized import or signature {row['module']}.{row['name']}")
    if memory_types and memory_types[0] != profile.address_bits:
        raise ValueError("primary linear memory width differs from the selected LLVM guest ABI")
    if not allow_memory64 and 64 in memory_types:
        raise ValueError("module declares a 64-bit memory with --no-memory64")
    if shared_memory_pages is not None and not selected_owner:
        raise ValueError("the final module does not import the selected shared memory")

def main(language, compile_native):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--sysroots", action="append", type=Path)
    parser.add_argument("--target", choices=("wasm32", "wasm64"), help="C/C++ pointer ABI (default: wasm32)")
    parser.add_argument("--memory64", action=argparse.BooleanOptionalAction, default=None,
                        help="allow 64-bit linear memory on the target VM (default: enabled for Core 3)")
    parser.add_argument("--core", choices=("mvp","3.0"))
    parser.add_argument("--eh", action=argparse.BooleanOptionalAction, default=None)
    if language == "cpp":
        parser.add_argument("--herbceptions", action=argparse.BooleanOptionalAction, default=True,
                            help="enable typed error returns (default), independently of traditional C++ EH")
    qualification.arguments(parser)
    optional_isa.arguments(parser)
    parser.add_argument("-pthread", "--threads", action="store_true", default=None)
    parser.add_argument("--no-threads", dest="threads", action="store_false", default=None)
    parser.add_argument("--shared-memory-pages", type=int, metavar="MAX",
                        help="import a bounded shared wasm32 env.memory (final link only)")
    model = parser.add_mutually_exclusive_group()
    model.add_argument("--reactor", action="store_true", help="provide your own guest entry point")
    model.add_argument("--wasi-reactor", action="store_true", help="use the WASIp1 reactor CRT and export _initialize")
    parser.add_argument("-l", "--link-library", dest="libraries", action="append", default=[],
                        help="link a named bundled WASIp1 archive after the application inputs")
    parser.add_argument("--export", action="append", default=[])
    parser.add_argument("-O", choices=list("0123sz"))
    parser.add_argument("-g", "--debug", dest="g", action="store_true", default=None)
    parser.add_argument("--no-debug", dest="g", action="store_false", default=None)
    parser.add_argument("-c", "--compile-only", action="store_true")
    parser.add_argument("-I", "--include-dir", action="append", default=[], type=Path)
    parser.add_argument("-D", "--define", action="append", default=[])
    parser.add_argument("--std", choices=("c11", "c17", "c23") if language == "c" else
                        ("c++98", "c++03", "c++11", "c++14", "c++17", "c++20", "c++23", "c++26"))
    if language == "cpp":
        parser.add_argument("-fconstexpr-steps", "--constexpr-steps", type=int, metavar="COUNT",
                            help="set Clang's C++ constant evaluation step limit")
    a = parser.parse_args()
    try:
        profile, selected = qualification.frontend_profile(a, language)
        a.memory64 = profile.memory64_enabled(a.memory64)
        if a.compile_only and a.shared_memory_pages is not None:
            raise ValueError("--shared-memory-pages is a final-link option")
        shared_flags = shared_memory_link_flags(profile, a.shared_memory_pages, wasi_crt=not a.reactor)
        library_flags = sysroot_link_flags(a.libraries, a.compile_only)
        disabled = optional_isa.restrictions(a, profile)
        if disabled and (a.require_qualified or selected is not None):
            raise ValueError("the selected strict release has no qualification for the reduced instruction set")
        admission = qualification.admit(language, a, profile, selected_release=selected)
        admission["optional_isa"] = optional_isa.receipt(a, profile)
        admission["memory64"] = a.memory64
        if any(not re.fullmatch(r"[a-zA-Z_]\w*", n,re.ASCII) for n in a.export):
            raise ValueError("invalid Wasm export name")
        sources=[p.resolve(strict=True) for p in a.sources]
        if a.output.resolve() in sources:
            raise ValueError("output aliases an input")
        if len(sources) > artifacts.MAX_MEMBERS:
            raise ValueError("too many compiler inputs")
        if any(p.suffix not in (".c",".cc",".cxx",".cpp",".C",".o",".a") for p in sources):
            raise ValueError("expected C/C++ sources or WROS .o/.a build artifacts")
        if a.compile_only and (len(sources) != 1 or sources[0].suffix in (".o", ".a") or a.reactor or a.wasi_reactor or a.export):
            raise ValueError("-c requires one source and no final-link options")
        if any(not re.fullmatch(r"[a-zA-Z_]\w*(?:=[^\r\n\x00]*)?", n, re.ASCII) for n in a.define):
            raise ValueError("invalid preprocessor definition")
        includes = [p.resolve(strict=True) for p in a.include_dir]
        if any(not p.is_dir() for p in includes):
            raise ValueError("include path is not a directory")
        with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
            staged=Path(td)/("unit.o" if a.compile_only else "module.wasm")
            args = ["-O" + a.O, *("-I" + str(p) for p in public_include_dirs(language)), *(["-g"] if a.g else [])]
            args += optional_isa.flags(a, profile)
            args += ["-I" + str(p) for p in includes] + ["-D" + n for n in a.define]
            if a.std: args += ["-std=" + a.std]
            if language == "cpp" and a.constexpr_steps is not None:
                if not 1 <= a.constexpr_steps <= 4294967295:
                    raise ValueError("constexpr steps must be a positive 32-bit count")
                args.append(f"-fconstexpr-steps={a.constexpr_steps}")
            if a.compile_only: args += ["-c"]
            if a.reactor: args += ["-nostartfiles","-Wl,--no-entry"]
            if a.wasi_reactor: args.append("-mexec-model=reactor")
            args += shared_flags
            args += ["-Wl,--export="+n for n in a.export]
            # Resolve the compiler/sysroot first; require that exact profile for
            # every separately compiled input. Copy validated object bytes into
            # our private work directory so later path replacement cannot race.
            command, record = make_command(a.toolchain, a.sysroots, profile, language, args,
                                           verify=True, herbceptions=getattr(a, "herbceptions", None))
            admission.update(compiler_sha256=record["compiler_sha256"], sysroot_sha256=record["closure_sha256"])
            if record["compiler_sha256"] != record["sysroot_producer_sha256"]:
                admission["sysroot_producer_sha256"] = record["sysroot_producer_sha256"]
            inputs = artifacts.stage_inputs(sources, Path(td), profile.to_dict(), record["compiler_sha256"], record["closure_sha256"], a.toolchain, qualification.object_releases(admission), disabled=disabled)
            if not a.compile_only:
                command.extend(optional_isa.link_flags(disabled, profile, record))
            command += [*map(str, inputs), "-o",str(staged)]
            if not a.compile_only:
                if "herbceptions_archive" in record:
                    command.append(record["herbceptions_archive"])
                # wasi-libc's compact formatter pulls stderr into even memory-only
                # snprintf calls via its unsupported long-double diagnostic.
                # The full formatter ships in the same verified guest sysroot.
                command.extend(library_flags)
            # Archive dependencies must precede libunwind in static link order.
            if "-lunwind" in command:
                command.remove("-lunwind")
                command.append("-lunwind")
            compile_native(command, record["compiler_sha256"])
            data = artifacts.read_bounded(staged)
            if a.compile_only:
                data = artifacts.seal_object(data, profile.to_dict(), record["compiler_sha256"], record["closure_sha256"], admission.get("release_sha256"), disabled=disabled)
            else:
                data = artifacts.strip_notes(data)
                audit(data, profile, a.shared_memory_pages, memory64=a.memory64)
                if a.shared_memory_pages is not None:
                    admission["shared_memory_pages"] = a.shared_memory_pages
            staged.write_bytes(data)
            qualification.finish(admission, a, staged, a.output)
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        parser.exit(1,f"{parser.prog}: {exc}\n")
    return 0
