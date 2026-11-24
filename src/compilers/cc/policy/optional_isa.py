"""Code generation choices shared by the four native C-family entry points."""
from pathlib import Path


def arguments(parser):
    for feature, description in (("simd128", "128-bit SIMD"),
                                 ("bulk-memory-opt", "memory.copy and memory.fill lowering")):
        key = feature.replace("-", "_")
        parser.add_argument("-m" + feature, dest=key, action="store_true", default=None,
                            help="enable " + description + " in application code")
        parser.add_argument("-mno-" + feature, dest=key, action="store_false", default=None,
                            help="disable " + description + " in application code")


def choices(options, profile):
    defaults = profile.wasm_version != "1.0"
    selected = {}
    for key in ("simd128", "bulk_memory_opt"):
        value = getattr(options, key, None)
        if value is True and not defaults:
            raise ValueError(f"{key.replace('_', '-')} requires Core 2.0 or later")
        selected[key] = defaults if value is None else value
    return selected


def flags(options, profile):
    # Leave the packaged target and old site/release defaults byte-for-byte
    # unchanged unless an application explicitly selects an instruction family.
    result = []
    if options.simd128 is False:
        result.extend(("-mno-relaxed-simd", "-mno-simd128"))
    elif options.simd128 is True:
        result.append("-msimd128")
    if options.bulk_memory_opt is False:
        if profile.threads:
            # Clang -pthread requires full bulk-memory for TLS/atomics, which
            # implies bulk-memory-opt in LLVM. Keep ordinary C memory calls as
            # calls. The linker can still introduce instructions independently.
            result.extend(("-fno-builtin-memcpy", "-fno-builtin-memmove", "-fno-builtin-memset"))
        else:
            result.extend(("-mno-bulk-memory", "-mno-bulk-memory-opt"))
    elif options.bulk_memory_opt is True:
        result.append("-mbulk-memory-opt")
    return result


def restrictions(options, profile):
    selected = choices(options, profile)
    return sorted(key for key, value in selected.items() if not value and profile.wasm_version != "1.0")


def receipt(options, profile):
    selected = choices(options, profile)
    return {**selected, "relaxed_simd": selected["simd128"] and profile.wasm_version == "3.0",
            "clang_flags": flags(options, profile), "scope": "application-code-generation",
            "linked_opcodes": "not-measured"}


def scalar_runtime(compiler, compile_job, profile, work):
    """Build scalar libc entry points with the admitted guest compiler and ABI."""
    source = Path(__file__).with_name("scalar_memory.c")
    obj = work / "wros-scalar-memory.o"
    compile_job([compiler, "--no-default-config", "--target=" + profile.triple,
                 *profile.llvm_feature_flags(), "-mno-relaxed-simd", "-mno-simd128",
                 *([] if profile.threads else ["-mno-bulk-memory", "-mno-bulk-memory-opt"]),
                 "-fsanitize=memtag" if profile.mte else "-fno-sanitize=memtag",
                 "-x", "c", "-std=c11", "-ffreestanding", "-nostdinc", "-O2", "-c", source, "-o", obj])
    return obj
