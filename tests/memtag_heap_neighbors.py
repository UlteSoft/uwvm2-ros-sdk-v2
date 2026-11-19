"""@brief Check registered heap colors across live allocations, resizing, retirement and GC."""
import argparse
import json
import os
from pathlib import Path
import resource
import re
import subprocess

from separate_compilation import Profile, ROOT, cgroup_record, inspect, sha, candidate_arguments, candidate_command
from compiler import compiler_environment, make_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + key, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--address-bits", type=int, nargs="+", choices=(32, 64), default=(32, 64))
    parser.add_argument("-O", choices=("2", "3"), default="3")
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--eh", action="store_true", help="exercise the tagged exception-enabled sysroot")
    parser.add_argument("--goroot", type=Path)
    parser.add_argument("--tinygoroot", type=Path)
    parser.add_argument("--host-cxx", type=Path)
    candidate_arguments(parser)
    args = parser.parse_args()
    standard_candidate = args.candidate_mte and json.loads(args.sysroots.read_bytes()).get("producer") != "herbceptions"
    if bool(args.goroot) != bool(args.tinygoroot):
        parser.error("TinyGo requires both --goroot and --tinygoroot")
    work = args.output
    receipt = {"complete": False, "cgroup": cgroup_record(), "cases": [], "modules": {}}
    work.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(work)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    c_source = ROOT / "tests/memtag/heap_neighbors.c"
    cpp_source = ROOT / "tests/memtag/heap_neighbors.cpp"
    go_source = ROOT / "tests/tinygo/heap_neighbors.go"
    unwind_sources = [ROOT / "tests/memtag/cxx_unwind.cpp", ROOT / "tests/memtag/cxx_unwind_observer.cpp"]
    inputs = [Path(__file__), c_source, cpp_source, ROOT / "bin/wrcc", args.toolchain / "bin/clang", args.toolchain / "bin/llvm-objdump",
              args.runtime, args.sysroots, ROOT / "bin/wrc"]
    if args.eh:
        inputs.extend(unwind_sources)
    if args.goroot:
        inputs.extend([go_source, ROOT / "bin/wrtg", ROOT / "language/tinygo/runtime/wros_gc.c"])
    receipt["inputs"] = {str(p): sha(p) for p in inputs}

    def save():
        (work / "results.json").write_text(json.dumps(receipt, indent=2) + "\n")

    def run(name, cmd, env=None):
        command = candidate_command(cmd, args.candidate_mte)
        result = subprocess.run(command, cwd=work, env=env, capture_output=True, timeout=240)
        (work / (name + ".stderr")).write_bytes(result.stderr)
        receipt["cases"].append({"name": name, "exit": result.returncode, "argv": command})
        save()
        if result.returncode:
            raise RuntimeError(name + ": " + result.stderr[-1500:].decode(errors="replace"))
        return result.stdout

    def execute(name, bits, module):
        imports = inspect(module.read_bytes())
        if imports:
            raise RuntimeError(name + ": unexpected host imports " + str(imports))
        assembly = run(name + "-disassemble", [args.toolchain / "bin/llvm-objdump", "-d", "--mattr=+memtag", module])
        # Attribute owner operations to the allocator itself. A stack claim
        # in the fixture, or a dead helper linked elsewhere, is insufficient.
        bodies = re.split(rb"(?m)^[0-9a-f]+ <([^>]+)>:\s*$", assembly)
        functions = dict(zip(bodies[1::2], bodies[2::2]))
        def locations(op):
            return [name.decode(errors="replace") for name, body in functions.items()
                    if re.search(rb"\bmemtag\." + op + rb"\b", body)]
        if name == "tinygo":
            rules = {b"claimz": {"wros_gc_claim"}, b"release": {"wros_gc_retire"}}
        else:
            rules = {b"claim": {"malloc", "dlmalloc_common_internal", "memtag_new_allocation", "internal_memalign",
                                "calloc", "aligned_alloc", "posix_memalign", "realloc", "memtag_resize"},
                     b"release": {"free", "dlfree", "realloc", "memtag_resize"}}
            if name.startswith("libc-"):
                rules[b"claimz"] = {"calloc", "dlmalloc_common_internal", "memtag_new_allocation"}
        owners = {op.decode(): locations(op) for op in rules}
        for op, expected in rules.items():
            if not (set(owners[op.decode()]) & expected):
                raise RuntimeError(f"{name}: no {op.decode()} in the expected allocator code; found {owners[op.decode()]}")
        (work / (name + ".asm")).write_bytes(assembly)
        receipt["modules"][name] = {"sha256": sha(module), "imports": imports, "owner_operations": owners}
        for engine in ("int", "aot"):
            launch = [args.runtime, *Profile(bits, mte=True, exceptions="noeh").uwvm_feature_flags(),
                      "--runtime-memtag-mode", "sync", "--runtime-memtag-backend", "software",
                      "--runtime-memtag-action", "crash", "--runtime-" + engine,
                      "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                      "--run", module]
            run(name + "-" + engine, launch)
            if name.startswith(("libc-", "libcxx-")):
                run(name + "-" + engine + "-runtime-off", [*launch[:-2], "--runtime-disable-memtag", *launch[-2:]])

    flags = ["--eh" if args.eh else "--no-eh", "--sysroots", args.sysroots, "--toolchain", args.toolchain, "-O" + args.O]
    if args.debug:
        flags.append("-g")

    def compile_cpp(name, bits, module, sources):
        """@brief Run the same C++ proof on a candidate's own libc++ and exception runtime."""
        if standard_candidate:
            # The stable C producer also builds libc++. Only the public wrcc
            # frontend requires the separate Herbceptions source patch set.
            profile = Profile(bits, exceptions="eh" if args.eh else "noeh")
            options = ["-O" + args.O, *(["-g"] if args.debug else []),
                       "-nostartfiles", "-Wl,--no-entry", "-Wl,--export=_start",
                       *map(str, sources), "-o", str(module)]
            command, _ = make_command(args.toolchain, [args.sysroots], profile, "cpp", options, verify=True)
            run(name + "-compile", command, compiler_environment(args.toolchain))
        else:
            run(name + "-compile", [ROOT / "bin/wrcc", "--target", "wasm" + str(bits), *flags,
                                    "--reactor", "--export", "_start", *sources, "-o", module])

    for bits in dict.fromkeys(args.address_bits):
        name = "libc-" + str(bits)
        module = work / (name + ".wasm")
        run(name + "-compile", [ROOT / "bin/wrc", "--target", "wasm" + str(bits), *flags,
                                "--reactor", "--export", "_start", c_source, "-o", module])
        execute(name, bits, module)
        name = "libcxx-" + str(bits)
        module = work / (name + ".wasm")
        compile_cpp(name, bits, module, [cpp_source])
        execute(name, bits, module)
        if args.eh:
            name = "unwind-" + str(bits)
            module = work / (name + ".wasm")
            compile_cpp(name, bits, module, unwind_sources)
            if inspect(module.read_bytes()):
                raise RuntimeError("freestanding exception fixture unexpectedly imports host operations")
            for engine in ("int", "aot"):
                launch = [args.runtime, *Profile(bits).uwvm_feature_flags(), "--runtime-" + engine,
                          "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                          "--runtime-memtag-mode", "sync", "--runtime-memtag-backend", "software",
                          "--run", module]
                run(name + "-" + engine, launch)
                run(name + "-" + engine + "-off", [*launch[:-2], "--runtime-disable-memtag", *launch[-2:]])
    if args.goroot:
        project = work / "go"
        project.mkdir()
        (project / "go.mod").write_text("module wros.local/neighbors\n\ngo 1.24\n")
        (project / "main.go").write_bytes(go_source.read_bytes())
        module = work / "tinygo.wasm"
        run("tinygo-compile", [ROOT / "bin/wrtg", project, "--eh" if args.eh else "--no-eh", "--sysroots", args.sysroots, "--toolchain", args.toolchain, "--goroot", args.goroot.resolve(),
                               "--tinygoroot", args.tinygoroot.resolve(), *(["--host-cxx", args.host_cxx] if args.host_cxx else []), "-o", module])
        execute("tinygo", 32, module)
    receipt["complete"] = all(sha(Path(p)) == d for p, d in receipt["inputs"].items())
    save()
    if not receipt["complete"]:
        raise RuntimeError("qualification input changed")


if __name__ == "__main__":
    main()
