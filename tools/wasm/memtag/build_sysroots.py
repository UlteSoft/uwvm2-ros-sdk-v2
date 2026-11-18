#!/usr/bin/env python3
"""Build stable, source-locked WASIp1 libc/CRT/C++ closures for the MTE producer.

Artifacts remain in --work until execution and safety qualification succeeds.
There is no host library fallback and no download during a component build.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from build_producer import SDK, HERE, digest, prepare, checked, inventory

sys.path.insert(0, str(SDK / "install"))
from guest_profile import Profile
from compiler import compiler_environment


def source_tree(entry, supplied, work, cache):
    if supplied is None:
        return prepare(entry, work, cache)
    source = supplied.resolve()
    # Reuse an existing private checkout without trusting its directory name.
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if revision != entry["revision"]:
        raise ValueError("source checkout does not match the stable revision")
    # Build the expected Git index from the release and each locked patch in
    # order. Compare the checkout against that index, including added files.
    # The checkout's index and object database remain available to its owner.
    work.mkdir(parents=True, exist_ok=True)
    objects = subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-path", "objects"], cwd=source, text=True).strip()
    with tempfile.TemporaryDirectory(dir=work) as temporary:
        sandbox = Path(temporary)
        (sandbox / "objects").mkdir()
        environment = dict(os.environ, GIT_INDEX_FILE=str(sandbox / "index"),
                           GIT_OBJECT_DIRECTORY=str(sandbox / "objects"),
                           GIT_ALTERNATE_OBJECT_DIRECTORIES=objects)

        def git(*args):
            return subprocess.run(["git", *args], cwd=source, env=environment, check=True, capture_output=True)

        git("read-tree", entry["revision"])
        for patch in entry["patches"]:
            filename = SDK / patch["path"]
            if digest(filename) != patch["sha256"]:
                raise ValueError("source patch hash mismatch: " + patch["path"])
            git("apply", "--cached", "--whitespace=nowarn", str(filename))
        git("update-index", "--really-refresh")
        git("diff-files", "--quiet", "--no-ext-diff", "--")
        if git("ls-files", "--others", "-z").stdout:
            raise ValueError("unrecorded files in the supplied source checkout")
    return source


def diagnostics_overlay(source, entry, work):
    """Apply locked runtime-only changes without changing the producer tree.

    Only ancestors and files named by the patch are copied. Other source paths
    point to the already verified private source tree. An inventory detects
    changes to either overlay files or link destinations before reuse.
    """
    patch = SDK / entry["path"]
    if digest(patch) != entry["sha256"]:
        raise ValueError("runtime diagnostics patch digest mismatch")
    changed = []
    for line in patch.read_text().splitlines():
        if line.startswith("+++ b/"):
            path = Path(line[6:])
            if path.is_absolute() or ".." in path.parts or not (source / path).is_file():
                raise ValueError("runtime patch has an unsafe/missing source path")
            changed.append(path)
    if not changed:
        raise ValueError("runtime patch changes no source files")
    identity = hashlib.sha256((str(source) + entry["sha256"]).encode()).hexdigest()
    container = work / "diagnostics" / identity
    root = container / "source"
    record = container / "inventory.json"
    if record.is_file():
        if inventory(root) != json.loads(record.read_text()):
            raise ValueError("runtime diagnostics overlay changed")
        return root
    if container.exists():
        raise ValueError("incomplete runtime overlay; use a fresh work directory")
    root.mkdir(parents=True)

    def copy_directory(relative):
        for item in (source / relative).iterdir():
            if item.name == ".git":
                continue
            path = relative / item.name
            destination = root / path
            if path in changed:
                shutil.copyfile(item, destination)
            elif any(path in other.parents for other in changed):
                destination.mkdir()
                copy_directory(path)
            else:
                destination.symlink_to(item.resolve(), target_is_directory=item.is_dir())

    copy_directory(Path())
    checked(["git", "-c", "core.hooksPath=/dev/null", "init", "--quiet"], container / "patch.log", root)
    checked(["git", "apply", "--check", str(patch)], container / "patch.log", root)
    checked(["git", "apply", str(patch)], container / "patch.log", root)
    record.write_text(json.dumps(inventory(root), sort_keys=True) + "\n")
    return root


def require_allocation_policy(assembly, policy, bits):
    """Require actual managed lifetime lowering from this recipe's stack probe."""
    if policy != "managed-neighborhood":
        raise ValueError("unsupported source-lock allocation policy: " + str(policy))
    ops = re.findall(r"(?m)^\s*memtag\.([a-z0-9_]+)\b", assembly)
    lifetime = [op for op in ops if op in {"claim", "claimz", "reserve", "activate", "release"}]
    # This probe has one escaping local, a single straight-line path and one
    # return. There must be exactly one completed lifetime on that path.
    paired = lifetime in (["claim", "release"], ["claimz", "release"], ["reserve", "activate", "release"])
    if (not paired or
            any(op.startswith(("random", "hint")) or op in ("store", "storez", "untagstore", "untagstorez") for op in ops)):
        raise ValueError(f"producer lacks managed-neighborhood stack acquire/release for wasm{bits}")


def build(args):
    if args.jobs < 1:
        raise ValueError("--jobs must be positive")
    # Validate all requested axes before extracting or compiling anything.
    profiles = {}
    for target in args.targets:
        if target not in ("wasm32-wasip1", "wasm32-wasip1-threads", "wasm64-wasip1"):
            raise ValueError("no stable closure for " + target + "; memory64 threads still require VM/bootstrap support")
        for exception in args.profiles:
            profiles[target, exception] = Profile(
                address_bits=64 if target.startswith("wasm64-") else 32,
                wasm_version=args.wasm_version, threads=target.endswith("-threads"),
                mte=args.mte, exceptions=exception)
    work = args.work.resolve()
    if work == SDK or work in SDK.parents:
        raise ValueError("--work must be a dedicated build directory")
    work.mkdir(parents=True, exist_ok=True)
    previous = work / "sysroots.json"
    if previous.is_file() and json.loads(previous.read_text()).get("mte") != args.mte:
        raise ValueError("use a separate --work directory for each MTE mode to preserve sysroot receipts")
    toolchain = args.toolchain.resolve()
    environment = compiler_environment(toolchain)
    os.environ.clear()
    os.environ.update(environment)
    compiler = toolchain / "bin/clang"
    version = subprocess.check_output([str(compiler), "--version"], text=True)
    if "clang version 23.1.5" not in version:
        raise ValueError("the closure requires the stable LLVM 23.1.5 MTE producer")
    for name in ("clang", "clang++", "llvm-ar", "llvm-ranlib", "llvm-nm", "llvm-config", "wasm-ld"):
        if not (toolchain / "bin" / name).is_file():
            raise ValueError("missing explicit compiler tool: " + name)
    # Even the non-instrumented sysroot must come from a capable producer.
    # An escaping local forces observable Wasm tag code at both target widths.
    probe = "extern void observe(void *); void example(void) { char region[64]; observe(region); }"
    lock = json.loads((HERE / "source-lock.json").read_text())
    policy = lock["producer"]["allocation_policy"]
    capability = {}
    for bits in sorted({profile.address_bits for profile in profiles.values()}):
        command = [str(compiler), "--no-default-config", f"--target=wasm{bits}-wasip1",
                   "-O3", "-g", "-x", "c", "-S", "-fsanitize=memtag", "-o", "-", "-"]
        assembly = subprocess.run(command, input=probe, capture_output=True, text=True, check=True).stdout
        require_allocation_policy(assembly, policy, bits)
        capability[str(bits)] = hashlib.sha256(assembly.encode()).hexdigest()
    llvm = source_tree(lock["sources"]["llvm-23.1.5"], args.llvm_source, work, args.source_cache)
    libc = source_tree(lock["sources"]["wasi-libc-sdk34"], args.libc_source, work, args.source_cache)
    runtimes = diagnostics_overlay(llvm, lock["runtime_diagnostics"]["llvm"], work)
    libc = diagnostics_overlay(libc, lock["runtime_diagnostics"]["libc"], work)
    original_resource = Path(subprocess.check_output([str(compiler), "-print-resource-dir"], text=True).strip())
    if not (original_resource / "include/stddef.h").is_file():
        raise ValueError("compiler resource headers are missing")
    environment = {"LC_ALL": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": "1793664000", "ZERO_AR_DATE": "1",
                   "PYTHONDONTWRITEBYTECODE": "1"}
    os.environ.update(environment)
    record = {"schema": "uwvm-memtag-sysroot-build-v1", "qualified": False, "status": "building",
              "compiler_version": version, "compiler_sha256": digest(compiler), "sources": lock["sources"],
              "mte": args.mte, "wasm_version": args.wasm_version, "producer_mte_codegen": capability,
              "runtime_diagnostics": lock["runtime_diagnostics"], "producer_allocation_policy": policy,
              "targets": [], "commands": []}
    # Ninja does not treat the compiler executable as an object dependency.
    # Replacing clang at the same pathname must never reuse objects from the
    # previous producer. Namespace the component cache by its complete inputs.
    identity = {"recipe": "stable-sysroots-v3", "compiler": record["compiler_sha256"],
                "recipe_sha256": digest(Path(__file__)),
                "profile_recipe_sha256": digest(SDK / "install/guest_profile.py"),
                "sources": lock["sources"], "runtime_diagnostics": lock["runtime_diagnostics"],
                "mte": args.mte, "wasm_version": args.wasm_version,
                "archiver": digest(toolchain / "bin/llvm-ar"),
                "ranlib": digest(toolchain / "bin/llvm-ranlib")}
    build_identity = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    record["build_identity"] = build_identity
    receipt = work / "sysroots.json"
    receipt.write_text(json.dumps(record, indent=2) + "\n")

    def component(name, source, prefix, definitions):
        directory = work / "build" / build_identity / name
        log = work / "logs" / (name + ".log")
        log.parent.mkdir(exist_ok=True)
        common = {"CMAKE_BUILD_TYPE": "Release", "CMAKE_INSTALL_PREFIX": str(prefix),
                  "CMAKE_C_FLAGS_RELEASE": "-O3", "CMAKE_CXX_FLAGS_RELEASE": "-O3",
                  "CMAKE_ASM_FLAGS_RELEASE": "-O3",
                  "CMAKE_C_COMPILER": str(compiler), "CMAKE_CXX_COMPILER": str(toolchain / "bin/clang++"),
                  "CMAKE_ASM_COMPILER": str(compiler), "CMAKE_AR": str(toolchain / "bin/llvm-ar"),
                  "CMAKE_RANLIB": str(toolchain / "bin/llvm-ranlib"), "CMAKE_NM": str(toolchain / "bin/llvm-nm"),
                  "CMAKE_C_COMPILER_WORKS": "ON", "CMAKE_CXX_COMPILER_WORKS": "ON",
                  "CMAKE_C_LINKER_DEPFILE_SUPPORTED": "OFF", "CMAKE_CXX_LINKER_DEPFILE_SUPPORTED": "OFF",
                  "CMAKE_TRY_COMPILE_TARGET_TYPE": "STATIC_LIBRARY", "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"}
        common.update(definitions)
        commands = [[args.cmake, "-G", "Ninja", "-S", str(source), "-B", str(directory),
                     *["-D" + k + "=" + v for k, v in common.items()]],
                    [args.cmake, "--build", str(directory), "--parallel", str(args.jobs)],
                    [args.cmake, "--install", str(directory)]]
        for command in commands:
            record["commands"].append(command)
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            print(name + ": " + command[1], flush=True)
            checked(command, log)
        return directory

    for target in args.targets:
        if target not in ("wasm32-wasip1", "wasm32-wasip1-threads", "wasm64-wasip1"):
            raise ValueError("no stable closure for " + target + "; memory64 threads still require VM/bootstrap support")
        memory64 = target.startswith("wasm64-")
        target_libc = prepare(lock["sources"]["wasi-libc-sdk34-memory64"], work, args.source_cache) if memory64 else libc
        if memory64:
            target_libc = diagnostics_overlay(target_libc, lock["runtime_diagnostics"]["libc"], work)
        threads = target.endswith("-threads")
        resource = work / "output" / "clang" / "23"
        shutil.copytree(original_resource / "include", resource / "include", dirs_exist_ok=True)
        feature_flags = profiles[target, args.profiles[0]].llvm_feature_flags()
        flags = "-g -ffile-prefix-map=" + str(work) + "=/usr/src/uwvm-sysroot"
        flags += " -ffile-prefix-map=" + str(llvm) + "=/usr/src/llvm-23.1.5"
        flags += " -ffile-prefix-map=" + str(runtimes) + "=/usr/src/llvm-23.1.5"
        flags += " -ffile-prefix-map=" + str(target_libc) + "=/usr/src/wasi-libc-sdk34"
        flags += " " + " ".join(feature_flags)
        flags += " -D__WROS_NO_HOST_DIAGNOSTICS"
        flags += " -fsanitize=memtag" if args.mte else " -fno-sanitize=memtag"
        if threads:
            flags += " -pthread -matomics -mbulk-memory"
        common_target = {"CMAKE_SYSTEM_NAME": "WASI", "CMAKE_SYSTEM_PROCESSOR": "wasm64" if memory64 else "wasm32",
                         "CMAKE_C_COMPILER_TARGET": target, "CMAKE_CXX_COMPILER_TARGET": target,
                         "CMAKE_ASM_COMPILER_TARGET": target}
        builtin_prefix = work / "builtins" / target
        component("builtins-" + target, llvm / "compiler-rt/lib/builtins", builtin_prefix,
                  {**common_target, "CMAKE_C_FLAGS": flags + " -ffreestanding",
                   "CMAKE_CXX_FLAGS": flags + " -ffreestanding", "CMAKE_ASM_FLAGS": flags + " -fwasm-exceptions",
                   "COMPILER_RT_DEFAULT_TARGET_ONLY": "ON", "COMPILER_RT_BAREMETAL_BUILD": "ON",
                   "COMPILER_RT_BUILTINS_ENABLE_PIC": "OFF", "COMPILER_RT_HAS_FPIC_FLAG": "OFF",
                   "COMPILER_RT_INCLUDE_TESTS": "OFF", "LLVM_ENABLE_PER_TARGET_RUNTIME_DIR": "OFF",
                   "COMPILER_RT_OS_DIR": "wasi", "LLVM_CONFIG_PATH": str(toolchain / "bin/llvm-config")})
        builtins = list(builtin_prefix.rglob("libclang_rt.builtins*.a"))
        if len(builtins) != 1:
            raise ValueError("expected one freshly compiled builtins archive")
        lookup = Path(subprocess.check_output([str(compiler), "--target=" + target,
                      "-resource-dir=" + str(resource), "--print-libgcc-file-name"], text=True).strip())
        if resource not in lookup.parents:
            raise ValueError("compiler-rt resource destination escaped its prefix")
        lookup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(builtins[0], lookup)
        c_prefix = work / "libc" / target
        component("libc-" + target, target_libc, c_prefix,
                  {**common_target, "TARGET_TRIPLE": target, "CMAKE_C_FLAGS": flags,
                   "CMAKE_ASM_FLAGS": flags, "BUILTINS_LIB": str(lookup), "BUILD_SHARED": "OFF",
                   "SETJMP": "OFF", "BINDINGS_TARGET": "OFF", "BUILD_TESTS": "OFF",
                   "ENABLE_MEMTAG": "ON" if args.mte else "OFF", "MEMTAG_NOVERBOSE": "ON",
                   "USE_WASM_COMPONENT_LD": "OFF", "WASI_SDK_VERSION": "uwvm-stable-sdk34-mte"})
        for profile in args.profiles:
            prefix = work / "output" / profile / target
            shutil.copytree(c_prefix, prefix, dirs_exist_ok=True)
            enabled = "ON" if profile == "eh" else "OFF"
            runtime_flags = flags + " -resource-dir=" + str(resource)
            if profile == "eh":
                runtime_flags += " -fwasm-exceptions -mllvm -wasm-use-legacy-eh=false"
            component("cxx-" + profile + "-" + target, runtimes / "runtimes", prefix,
                      {**common_target, "CMAKE_SYSROOT": str(prefix),
                       # The complete libc and compiler-rt closure now exists.
                       # Library probes must link: archiving an unresolved symbol
                       # incorrectly reports __cxa_thread_atexit_impl and dladdr.
                       "CMAKE_TRY_COMPILE_TARGET_TYPE": "EXECUTABLE",
                       "CMAKE_C_FLAGS": runtime_flags,
                       "CMAKE_CXX_FLAGS": runtime_flags, "CMAKE_ASM_FLAGS": runtime_flags,
                       "LLVM_ENABLE_RUNTIMES": "libcxx;libcxxabi" + (";libunwind" if profile == "eh" else ""),
                       "LLVM_INCLUDE_TESTS": "OFF", "LLVM_ENABLE_PER_TARGET_RUNTIME_DIR": "OFF",
                       "LLVM_CONFIG_PATH": str(toolchain / "bin/llvm-config"), "UNIX": "ON",
                       "LIBCXX_HAS_MUSL_LIBC": "OFF", "LIBCXX_ENABLE_SHARED": "OFF", "LIBCXX_ENABLE_STATIC": "ON",
                       "LIBCXX_ENABLE_EXCEPTIONS": enabled, "LIBCXXABI_ENABLE_EXCEPTIONS": enabled,
                       "LIBCXX_ENABLE_THREADS": "ON" if threads else "OFF",
                       "LIBCXXABI_ENABLE_THREADS": "ON" if threads else "OFF",
                       "LIBCXX_DEBUG_SOURCE_DIR": "/usr/src/llvm-23.1.5/libcxx",
                       "LIBCXX_ENABLE_FILESYSTEM": "ON", "LIBCXX_ENABLE_ABI_LINKER_SCRIPT": "OFF",
                       "LIBCXX_CXX_ABI": "libcxxabi", "LIBCXX_ABI_VERSION": "2",
                       "LIBCXXABI_ENABLE_SHARED": "OFF", "LIBCXXABI_ENABLE_STATIC": "ON",
                       # Silent terminate alone does not remove __abort_message's
                       # stderr path. The upstream baremetal Wasm configuration
                       # traps on ABI corruption without importing descriptor
                       # I/O, its stdio locks, or their WASIp1 clock dependency.
                       # ARM-specific baremetal unwind changes do not apply to
                       # the WebAssembly-only producer.
                       "LIBCXXABI_BAREMETAL": "ON",
                       "LIBCXXABI_SILENT_TERMINATE": "ON", "LIBCXXABI_USE_LLVM_UNWINDER": enabled,
                       "LIBUNWIND_ENABLE_SHARED": "OFF", "LIBUNWIND_ENABLE_THREADS": "ON" if threads else "OFF",
                       "LIBUNWIND_HIDE_SYMBOLS": "ON", "LIBUNWIND_USE_COMPILER_RT": "ON",
                       "LIBUNWIND_INCLUDE_TESTS": "OFF", "LIBCXX_INCLUDE_TESTS": "OFF",
                       "LIBCXX_INCLUDE_BENCHMARKS": "OFF", "LIBCXXABI_INCLUDE_TESTS": "OFF",
                       "LIBCXX_INSTALL_MODULES": "OFF", "LIBCXX_LIBDIR_SUFFIX": "/" + target,
                       "LIBCXXABI_LIBDIR_SUFFIX": "/" + target, "LIBUNWIND_LIBDIR_SUFFIX": "/" + target})
            # Resource headers and builtins are part of the compiler closure,
            # not optional host inputs. Include them in --verify coverage.
            files = {str(p.relative_to(work)): digest(p)
                     for base in (prefix, resource) for p in base.rglob("*") if p.is_file()}
            record["targets"].append({"triple": target, "profile": profile, "threads": threads,
                                      "guest_profile": profiles[target, profile].to_dict(),
                                      "feature_flags": feature_flags,
                                      "sysroot": str(prefix.relative_to(work)), "resource": str(resource.relative_to(work)),
                                      "builtins_sha256": digest(lookup), "files": files, "qualified": False})
            receipt.write_text(json.dumps(record, indent=2) + "\n")
    record["status"] = "built-awaiting-qualification"
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(receipt, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--toolchain", type=Path, required=True)
    parser.add_argument("--llvm-source", type=Path)
    parser.add_argument("--libc-source", type=Path)
    parser.add_argument("--source-cache", type=Path)
    parser.add_argument("--targets", nargs="+", default=["wasm32-wasip1-threads"])
    parser.add_argument("--profiles", nargs="+", choices=["noeh", "eh"], default=["noeh"])
    parser.add_argument("--wasm-version", choices=["1.0", "2.0", "3.0"], default="3.0")
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--cmake", default="cmake")
    try:
        build(parser.parse_args())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
