"""Build a Fortran PROGRAM with Flang, the WasmMTE LLVM backend and the SDK linker."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "third-parties/fortran"
sys.path.insert(0, str(ROOT / "install"))
from artifacts import archive_members, read_bounded, seal_object
from imports import inspect
from compiler import compiler_environment, make_command
from prepare import require_marker
from flang_identity import require_compiler
from guest_profile import Profile
import qualification
KINDS = {"i32": ("int32_t", 4), "i64": ("int64_t", 8)}
FORMS = {".f90", ".f95", ".f03", ".f08", ".f18"}


def write_bindings(work):
    """Generate matching ISO integer kind declarations and signed Wasm imports."""
    schema = json.loads((ROOT / "share/abi/ros.json").read_text())
    declarations = ["module wros_scene", "  implicit none", "  interface"]
    # The ABI transports addresses as i64 for both guest pointer widths.
    # uintptr_t preserves tag bits and zero-extends wasm32 addresses.
    declarations.extend(["    function wr_address(pointer) result(bits) bind(c)",
                         "      use iso_c_binding, only: c_ptr, c_int64_t",
                         "      type(c_ptr), value :: pointer",
                         "      integer(c_int64_t) :: bits", "    end function"])
    header = ["#include <stdint.h>", "int64_t wr_address(const void *pointer) {",
              "  uint64_t bits = (uintptr_t)pointer;", "  int64_t result;",
              "  __builtin_memcpy(&result, &bits, sizeof result);", "  return result;", "}"]
    for operation in schema["operations"]:
        name = operation["name"]
        symbol = "wr_" + name.replace(".", "_").replace("-", "_")
        signature = operation["wasm_signature"]
        if (not re.fullmatch(r"[a-z][a-z0-9_.-]*", name) or len(symbol) > 63
                or signature["results"] != ["i32"]):
            raise ValueError("unsupported ROS ABI operation " + name)
        params = [KINDS[code] for code in signature["parameters"]]
        args = [f"a{i}" for i in range(len(params))]
        declarations.append(f"    integer(kind=4) function {symbol}({', '.join(args)}) bind(c)")
        for arg, (_, kind) in zip(args, params):
            declarations.append(f"      integer(kind={kind}), value :: {arg}")
        declarations.append("    end function")
        types = ", ".join(t for t, k in params) or "void"
        qualified = ", ".join(f"{t} {arg}" for (t, _), arg in zip(params, args)) or "void"
        header.append(f'__attribute__((import_module("{schema["module"]}"), import_name("{name}"))) '
                      f'extern int32_t host_{symbol}({types});')
        header.append(f'int32_t {symbol}({qualified}) {{ return host_{symbol}({", ".join(args)}); }}')
    declarations.extend(["  end interface", "end module"])
    (work / "wros_scene.f90").write_text("\n".join(declarations) + "\n")
    (work / "wros_imports.c").write_text("\n".join(header) + "\n")


def link_program(arguments, work, env):
    """Reject LLD's synthetic runtime trap for an incompatible foreign definition."""
    with tempfile.TemporaryFile(dir=work) as diagnostics:
        result = subprocess.run(arguments, cwd=work, env={**env, "LC_ALL": "C"}, stderr=diagnostics)
        diagnostics.seek(0)
        mismatch = False
        for line in diagnostics:
            sys.stderr.buffer.write(line)
            if b"wasm-ld: warning: function signature mismatch:" in line:
                mismatch = True
    result.check_returncode()
    if mismatch:
        raise ValueError("a linked definition has an incompatible WebAssembly function signature")


def lower_unit(compiler, marker, toolchain, receipts, profile, fc, opts, source, work, i, release):
    """Keep every user function in the common LLVM optimization/MTE pipeline."""
    ir, bc, obj = [work / (str(i) + suffix) for suffix in (".ll", ".bc", ".o")]
    env = compiler_environment(toolchain)
    if opts.g:
        fc = [*fc, "-debug-info-kind=standalone"]
    subprocess.run([compiler, *fc, "-emit-llvm", "-O0", source, "-o", ir], check=True, cwd=work, env=env)
    subprocess.run([marker, str(profile.address_bits), "on" if profile.mte else "off", ir, bc], check=True, cwd=work, env=env)
    flags = ["-O" + opts.O, "-x", "ir", "-c"]
    if opts.g:
        flags.append("-g")
    cmd, provenance = make_command(toolchain, receipts, profile, "c", flags, verify=True)
    subprocess.run([*cmd, bc, "-o", obj], check=True, cwd=work, env=env)
    obj.write_bytes(seal_object(read_bounded(obj), profile.to_dict(), provenance["compiler_sha256"], provenance["closure_sha256"], release))
    return obj


# Flang generates one external entry point per operation and operand kind.
# These families are implemented by separate upstream translation units.
TRANSFORMATIONS = frozenset("Cshift CshiftVector Eoshift EoshiftVector Pack Reshape ShallowCopy "
                            "ShallowCopyDirect Spread Transpose Unpack".split())
LOGICAL_REDUCTIONS = frozenset("All AllDim Any AnyDim Count CountDim Parity ParityDim".split())


def array_intrinsic_unit(name):
    """Choose the upstream guest implementation for an unresolved Flang entry point."""
    if name in TRANSFORMATIONS:
        return "transformational"
    if name in LOGICAL_REDUCTIONS or re.fullmatch(r"I(?:All|Any|Parity)(?:1|2|4|8|16|Dim)", name):
        return "reduction"
    if name == "SumDim" or re.fullmatch(r"Sum(?:(?:Integer|Unsigned)(?:1|2|4|8|16)|Real(?:4|8))", name):
        return "sum"
    if name == "DotProductLogical" or re.fullmatch(r"DotProductReal[48]", name):
        return "dot-product-real"
    if re.fullmatch(r"DotProduct(?:Integer|Unsigned)(?:1|2|4|8|16)", name):
        return "dot-product-integer"
    pair = re.fullmatch(r"Matmul(?:Direct)?(Integer|Logical|Real|Unsigned)[1248](Integer|Logical|Real|Unsigned)[1248]", name)
    if pair:
        kinds = set(pair.groups())
        if kinds in ({"Integer"}, {"Logical"}):
            return "matmul-integer"
        if "Real" in kinds and kinds <= {"Real", "Integer", "Unsigned"}:
            return "matmul-real"
    return None


def runtime_requirements(inputs):
    """Inspect unresolved guest symbols once, including sealed static archive members."""
    prefixes = ("_FortranAAllocatable", "_FortranAAssign", "_FortranACopyInAssign",
                "_FortranACopyOutAssign", "_FortranAMoveAlloc", "_FortranAPointer", "CFI_")
    descriptors = False
    clocks = False
    intrinsics = set()
    for path in inputs:
        data = read_bounded(path)
        members = archive_members(data) if path.suffix == ".a" else (data,)
        for member in members:
            for item in inspect(member):
                if item["module"] != "env":
                    continue
                name = item["name"]
                if name in ("_FortranASystemClockCount", "_FortranASystemClockCountRate",
                            "_FortranASystemClockCountMax", "_FortranACpuTime"):
                    clocks = True
                if name.startswith(prefixes):
                    descriptors = True
                if name.startswith("_FortranA"):
                    unit = array_intrinsic_unit(name.removeprefix("_FortranA"))
                    if unit:
                        intrinsics.add(unit)
    return descriptors or bool(intrinsics), sorted(intrinsics), clocks


def guest_runtime(command, env, work, toolchain, descriptors, intrinsics):
    """Compile the target's numerical and selected descriptor/array runtime procedures."""
    includes = [VENDOR / "flang/include", VENDOR / "flang-rt/include"]
    runtime = VENDOR / "flang-rt/lib/runtime"
    sources = [runtime / (unit + ".cpp") for unit in ("numeric", "complex-powi")]
    options = []
    if descriptors:
        # Flang's compute work queue omits external I/O tickets under this option.
        options.append("-DRT_CUDA_THIN_IO=1")
        includes.append(runtime)
        units = ("ISO_Fortran_binding", "allocatable", "allocator-registry", "assign",
                 "copy", "derived", "descriptor", "memory", "pointer", "stat", "tools",
                 "type-code", "type-info", "work-queue")
        sources.extend(runtime / (unit + ".cpp") for unit in (*units, *intrinsics))
        sources.append(ROOT / "language/fortran/compute_platform.cpp")
    flags = ["--std", "c++17", *options, *(arg for p in includes for arg in ("-I", p))]
    objects = []
    for source in sources:
        obj = work / (source.stem + ".o")
        subprocess.run([*command, *flags, "-c", source, "-o", obj],
                       check=True, env=env, cwd=work)
        objects.append(obj)
    archive = work / "libflang-compute.a"
    subprocess.run([sys.executable, "-B", ROOT / "bin/wrar", "--toolchain", toolchain, *objects, "-o", archive],
                   check=True, env=env, cwd=work)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path, help="Fortran files in module dependency order")
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("--sysroots", required=True, action="append", type=Path)
    parser.add_argument("--flang", type=Path, help="WROS-patched Flang (default TOOLCHAIN/bin/flang)")
    parser.add_argument("--mte-tool", type=Path, help="prepared LLVM helper (default TOOLCHAIN/bin/wros-flang-mte)")
    parser.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    parser.add_argument("-O", choices=list("0123sz"), default="3")
    parser.add_argument("-g", action="store_true")
    parser.add_argument("--core", choices=("mvp", "3.0"), default="3.0")
    parser.add_argument("--eh", action=argparse.BooleanOptionalAction, default=None)
    qualification.arguments(parser)
    parser.add_argument("-pthread", "--threads", action="store_true")
    parser.add_argument("--static", action="store_true", help="emit a checked Wasm archive of the Fortran source units")
    parser.add_argument("--link-object", action="append", type=Path, default=[],
                        help="WROS-sealed guest object/archive for the selected profile")
    parser.add_argument("-o", "--output", required=True, type=Path)
    opts = parser.parse_args()
    try:
        sources = [p.resolve(strict=True) for p in opts.sources]
        objects = [p.resolve(strict=True) for p in opts.link_object]
        if len(sources) > 256 or sum(p.stat().st_size for p in sources) > 16 * 1024 * 1024:
            raise ValueError("expected up to 256 Fortran files totalling at most 16 MiB")
        if any(p.suffix.lower() not in FORMS | {".f", ".for", ".ftn"} for p in sources):
            raise ValueError("expected Fortran source")
        if any(p.suffix not in (".o", ".a") for p in objects):
            raise ValueError("expected sealed .o/.a link inputs")
        output = opts.output.resolve()
        if opts.static and (opts.build_receipt or objects or output.suffix != ".a"):
            raise ValueError("a static library requires Fortran source files and a .a output without a deployment receipt")
        if output in sources or output in objects:
            raise ValueError("output aliases an input")
        toolchain = opts.toolchain.resolve(strict=True)
        receipts = [p.resolve(strict=True) for p in opts.sysroots]
        compiler = (opts.flang or toolchain / "bin/flang").resolve(strict=True)
        marker = (opts.mte_tool or toolchain / "bin/wros-flang-mte").resolve(strict=True)
        env = compiler_environment(toolchain)
        bits = int(opts.target[4:])
        eh = opts.core == "3.0" if opts.eh is None else opts.eh
        profile = Profile(bits, wasm_version="1.0" if opts.core == "mvp" else "3.0",
                          threads=opts.threads, mte=opts.mte, exceptions="eh" if eh else "noeh")
        admission = qualification.admit("fortran", opts, profile, {"flang": compiler, "marker": marker})
        require_compiler(compiler)
        require_marker(marker, toolchain)
        with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
            work = Path(scratch)
            fc = ["-fc1", "-triple", opts.target + "-unknown-wasip1",
                  "-module-dir", work, "-fintrinsic-modules-path", work, "-I", work]
            write_bindings(work)
            mod_dir = VENDOR / "flang-rt/lib/runtime"
            for name in ("__fortran_builtins", "iso_c_binding", "iso_fortran_env_impl", "iso_fortran_env"):
                subprocess.run([compiler, *fc, "-cpp", "-fsyntax-only", mod_dir / (name + ".f90")],
                               check=True, cwd=work, env=env)
            subprocess.run([compiler, *fc, "-fsyntax-only", work / "wros_scene.f90"], check=True, cwd=work, env=env)
            units = [lower_unit(compiler, marker, toolchain, receipts, profile, fc, opts, source, work, i, admission.get("release_sha256"))
                     for i, source in enumerate(sources)]
            if opts.static:
                # Runtime calls in these sealed source units resolve when an application links the archive.
                staged = work / "guest.a"
                subprocess.run([sys.executable, "-B", ROOT / "bin/wrar", "--toolchain", toolchain,
                                *units, "-o", staged], check=True, cwd=work, env=env)
                qualification.finish(admission, opts, staged, output)
                return 0
            flags = ["--toolchain", toolchain, "--target", opts.target, "-O" + opts.O]
            for receipt in receipts:
                flags.extend(("--sysroots", receipt))
            flags.extend(("--core", opts.core, "--eh" if eh else "--no-eh", qualification.switch(opts)))
            if opts.threads:
                flags.append("--threads")
            if opts.g:
                flags.append("-g")
            descriptors, intrinsics, clocks = runtime_requirements([*units, *objects])
            cc = [sys.executable, "-B", ROOT / "bin/wrc", *flags]
            cxx = [sys.executable, "-B", ROOT / "bin/wrcc", *flags]
            runtime = guest_runtime(cxx, env, work, toolchain, descriptors, intrinsics)
            stubs = []
            bridge_sources = [work / "wros_imports.c", ROOT / "language/fortran/entry.c"]
            if clocks:
                bridge_sources.append(ROOT / "language/fortran/clock.c")
            for source in bridge_sources:
                obj = work / (source.stem + ".o")
                subprocess.run([*cc, "-c", source, "-o", obj], check=True, cwd=work, env=env)
                stubs.append(obj)
            # The upstream descriptor work queue uses libc++'s std::variant.
            linker = cxx if descriptors else cc
            staged = work / "guest.wasm"
            link_program([*linker, "--reactor", "--export", "_start", *units, *stubs,
                          *objects, runtime, "-o", staged], work, env)
            qualification.finish(admission, opts, staged, output)
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"wrf: {exc}\n")
