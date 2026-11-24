"""Build the selected WASIp1 sysroot from the SDK's LLVM and wasi-libc source trees."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from compiler import digest
from guest_profile import RUNTIME_ISA_FLAGS
from herbceptions_sysroot import TOOLS, definitions as domain_definitions, install_domains, verify_exception_bridge

HERE = Path(__file__).resolve().parent


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


def build(args, toolchain, work, source_sha256, provenance, prof):
    from rebuild import checked
    work.mkdir(parents=True, exist_ok=True)
    llvm = HERE / "llvm-project"
    runtimes = llvm
    target_libc = HERE / "wasi-libc"
    compiler = toolchain / "bin/clang"
    target, threads, profile = prof.triple, prof.threads, prof.exceptions
    release_name = "llvm-23.1.5"
    version = subprocess.check_output([compiler, "--version"], text=True)
    if not re.search(r"\bclang version 23\.1\.5(?:\s|$)", version):
        raise ValueError("expected LLVM Clang 23.1.5")
    probe = f'_Static_assert(sizeof(void *) * 8 == {prof.address_bits}, "incorrect guest pointer width");\n'
    probe += "extern void observe(int *); void wros_probe(void){ int value=1; observe(&value); }"
    command = [compiler, "--no-default-config", "--target=" + target, "-O3", "-g", "-x", "c", "-S",
               "-fsanitize=memtag", "-o", "-", "-"]
    assembly = subprocess.run(command, input=probe, text=True, stdout=subprocess.PIPE, check=True).stdout
    require_allocation_policy(assembly, "managed-neighborhood", prof.address_bits)
    capability = {str(prof.address_bits): hashlib.sha256(assembly.encode()).hexdigest()}
    original_resource = Path(subprocess.check_output([str(compiler), "-print-resource-dir"], text=True).strip())
    if not (original_resource / "include/stddef.h").is_file():
        raise ValueError("compiler resource headers are missing")
    environment = {"LC_ALL": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": "1793664000", "ZERO_AR_DATE": "1",
                   "PYTHONDONTWRITEBYTECODE": "1"}
    os.environ.update(environment)
    host_hashes = {name: digest(toolchain / "bin" / name) for name in TOOLS}
    record = {"sources_sha256": source_sha256, "tool_sha256": host_hashes, "compiler_version": version.strip(),
              "schema": "uwvm-memtag-sysroot-build-v1", "qualified": False, "status": "building",
              "compiler_sha256": host_hashes["clang"], "sources": provenance["upstreams"], "mte": prof.mte,
              "producer": "herbceptions", "herbceptions_runtime": True, "wasm_version": prof.wasm_version,
              "producer_allocation_policy": "managed-neighborhood", "producer_mte_codegen": capability,
              "targets": [], "commands": []}
    record["recipes_sha256"] = {name: digest(HERE / name)
                                for name in ("build_sysroot.py", "herbceptions_sysroot.py", "policy/guest_profile.py", "policy/scalar_memory.c")}
    identity = {"tools": host_hashes, "profile": prof.to_dict(), "sources_sha256": source_sha256,
                "recipes": record["recipes_sha256"]}
    build_identity = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    record["build_identity"] = build_identity
    # Keep install trees as well as Ninja objects separate when a recipe or tool changes.
    work = work / build_identity
    work.mkdir(parents=True, exist_ok=True)
    receipt = work / "sysroots.json"

    def component(name, source, prefix, definitions):
        directory = work / "build" / name
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

    resource = work / "output" / "clang" / "23"
    shutil.copytree(original_resource / "include", resource / "include", dirs_exist_ok=True)
    feature_flags = prof.llvm_feature_flags()
    flags = "-g -ffile-prefix-map=" + str(work) + "=/usr/src/uwvm-sysroot"
    flags += " -ffile-prefix-map=" + str(work / "build") + "=/usr/src/uwvm-build"
    flags += " -ffile-prefix-map=" + str(original_resource) + "=/usr/src/clang-resource/23"
    flags += " -ffile-prefix-map=" + str(llvm) + "=/usr/src/" + release_name
    flags += " -ffile-prefix-map=" + str(runtimes) + "=/usr/src/" + release_name
    flags += " -ffile-prefix-map=" + str(target_libc) + "=/usr/src/wasi-libc-sdk34"
    flags += " " + " ".join([*feature_flags, *RUNTIME_ISA_FLAGS])
    flags += " -ffile-prefix-map=" + str(HERE / "policy") + "=/usr/src/wros-runtime"
    flags += " -D__WROS_NO_HOST_DIAGNOSTICS"
    flags += " -fsanitize=memtag" if prof.mte else " -fno-sanitize=memtag"
    common_target = {"CMAKE_SYSTEM_NAME": "WASI", "CMAKE_SYSTEM_PROCESSOR": f"wasm{prof.address_bits}",
                     "CMAKE_C_COMPILER_TARGET": target, "CMAKE_CXX_COMPILER_TARGET": target,
                     "CMAKE_ASM_COMPILER_TARGET": target}
    builtin_prefix = work / "builtins" / target
    component("builtins-" + target, llvm / "compiler-rt/lib/builtins", builtin_prefix,
              {**common_target, "CMAKE_C_FLAGS": flags + " -ffreestanding",
               "CMAKE_CXX_FLAGS": flags + " -ffreestanding", "CMAKE_ASM_FLAGS": flags,
               "COMPILER_RT_DEFAULT_TARGET_ONLY": "ON", "COMPILER_RT_BAREMETAL_BUILD": "ON",
               "COMPILER_RT_BUILTINS_ENABLE_PIC": "OFF", "COMPILER_RT_HAS_FPIC_FLAG": "OFF",
               "COMPILER_RT_INCLUDE_TESTS": "OFF", "LLVM_ENABLE_PER_TARGET_RUNTIME_DIR": "OFF",
               "COMPILER_RT_OS_DIR": "wasi",
               # Use the monorepo CMake modules, including when only the host executables are installed.
               "CMAKE_DISABLE_FIND_PACKAGE_LLVM": "ON"})
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
               "CMAKE_ASM_FLAGS": flags, "BUILTINS_LIB": str(lookup),
               "WROS_SCALAR_MEMORY_SOURCE": str(HERE / "policy/scalar_memory.c"), "SIMD": "OFF", "BUILD_SHARED": "OFF",
               "SETJMP": "OFF", "BINDINGS_TARGET": "OFF", "BUILD_TESTS": "OFF",
               "ENABLE_MEMTAG": "ON" if prof.mte else "OFF", "MEMTAG_NOVERBOSE": "ON",
               "USE_WASM_COMPONENT_LD": "OFF", "WASI_SDK_VERSION": "uwvm-stable-sdk34-" + ("mte" if prof.mte else "nomte")})
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
               "CMAKE_CXX_FLAGS": runtime_flags if profile == "eh" else runtime_flags + " -fno-exceptions",
               "CMAKE_ASM_FLAGS": runtime_flags,
               "LLVM_ENABLE_RUNTIMES": "libcxx;libcxxabi" + (";libunwind" if profile == "eh" else ""),
               "LLVM_INCLUDE_TESTS": "OFF", "LLVM_INCLUDE_DOCS": "OFF", "LLVM_ENABLE_PER_TARGET_RUNTIME_DIR": "OFF",
               "UNIX": "ON",
               "LIBCXX_HAS_MUSL_LIBC": "OFF", "LIBCXX_ENABLE_SHARED": "OFF", "LIBCXX_ENABLE_STATIC": "ON",
               "LIBCXX_ENABLE_EXCEPTIONS": enabled, "LIBCXXABI_ENABLE_EXCEPTIONS": enabled,
               "LIBCXXABI_ENABLE_HERBCEPTIONS_ERROR_DOMAIN": enabled,
               "LIBCXX_ENABLE_THREADS": "ON" if threads else "OFF",
               "LIBCXXABI_ENABLE_THREADS": "ON" if threads else "OFF",
               "LIBCXX_DEBUG_SOURCE_DIR": "/usr/src/" + release_name + "/libcxx",
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
               "LIBUNWIND_INCLUDE_DOCS": "OFF", "LIBCXX_INCLUDE_DOCS": "OFF",
               "LIBUNWIND_INCLUDE_TESTS": "OFF", "LIBCXX_INCLUDE_TESTS": "OFF",
               "LIBCXX_INCLUDE_BENCHMARKS": "OFF", "LIBCXXABI_INCLUDE_TESTS": "OFF",
               "LIBCXX_INSTALL_MODULES": "OFF", "LIBCXX_LIBDIR_SUFFIX": "/" + target,
               "LIBCXXABI_LIBDIR_SUFFIX": "/" + target, "LIBUNWIND_LIBDIR_SUFFIX": "/" + target})
    stage = work / "domains"
    component("herbceptions-" + profile + "-" + target, llvm / "libherbceptions", stage,
              domain_definitions(prefix, runtime_flags, common_target))
    domain = {"herbceptions": install_domains(stage, prefix, target, toolchain)}
    domain["herbceptions"]["legacy_exception_bridge"] = verify_exception_bridge(
        prefix, target, toolchain, profile == "eh")
    # Resource headers and builtins are part of the compiler closure,
    # not optional host inputs. Include them in --verify coverage.
    files = {str(p.relative_to(work)): digest(p)
             for base in (prefix, resource) for p in base.rglob("*") if p.is_file()}
    record["targets"].append({"triple": target, "profile": profile, "threads": threads,
                              "guest_profile": prof.to_dict(),
                              "feature_flags": feature_flags, "runtime_isa_flags": list(RUNTIME_ISA_FLAGS),
                              "sysroot": str(prefix.relative_to(work)), "resource": str(resource.relative_to(work)),
                              "builtins_sha256": digest(lookup), "files": files, "qualified": False, **domain})
    record["status"] = "built-awaiting-qualification"
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    return receipt
