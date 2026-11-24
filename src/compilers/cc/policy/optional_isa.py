"""Code generation choices shared by the four native C-family entry points."""
from guest_profile import RUNTIME_ISA_FLAGS


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
        # LLVM keeps the full bulk-memory feature for TLS and passive segments.
        # Suppress memory-intrinsic selection separately, including aggregate
        # assignments and explicit builtins. The verified libc supplies libcalls.
        result.extend(("-mllvm", "-wasm-disable-bulk-memory-opt"))
        if not profile.threads:
            result.extend(("-mno-bulk-memory", "-mno-bulk-memory-opt"))
    elif options.bulk_memory_opt is True:
        result.append("-mbulk-memory-opt")
    return result


def restrictions(options, profile):
    selected = choices(options, profile)
    return sorted(key for key, value in selected.items() if not value and profile.wasm_version != "1.0")


def link_flags(disabled, profile, record):
    if disabled and record.get("runtime_isa_flags") != list(RUNTIME_ISA_FLAGS):
        raise ValueError("disabled ISA switches require the scalar-baseline SDK sysroot for this profile")
    if "bulk_memory_opt" in disabled and profile.threads:
        return ["-Wl,-mllvm,-wasm-scalar-bss", "-Wl,--undefined=__wros_scalar_zero_bss"]
    return []


def receipt(options, profile):
    selected = choices(options, profile)
    return {**selected, "relaxed_simd": selected["simd128"] and profile.wasm_version == "3.0",
            "clang_flags": flags(options, profile), "scope": "application-and-sdk-runtime-code-generation",
            "linked_opcodes": "not-measured"}
