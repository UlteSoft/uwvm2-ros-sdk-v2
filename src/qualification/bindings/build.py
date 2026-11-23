"""Compile independent per-language users inside the qualification namespace."""
from collections import defaultdict
import json
from pathlib import Path
import shlex
import shutil
import subprocess

ROOT = Path("/work")
BINDINGS = ROOT / "include/u2rosv2/universal"
USERS = ROOT / "users"
OUT = ROOT / "out"
CONTRACT = json.loads((ROOT / "src/abi/contract.json").read_text())
DOMAINS = defaultdict(list)
for op in CONTRACT["operations"]:
    DOMAINS[op["domain"]].append(op)


def run(*args):
    argv = [str(arg) for arg in args]
    print(shlex.join(argv), flush=True)
    subprocess.run(argv, check=True)


def raw_symbol(op):
    return "uwrosv2_raw_" + op["name"].replace(".", "_")


def rust_member(op):
    domain = op["domain"]
    prefix = "module.call." if domain == "module_call" else op["name"].split(".")[0] + "."
    return op["name"].removeprefix(prefix).replace(".", "_")


def c_cxx_build(language, clang, mode, suffix, standard):
    include = BINDINGS / language
    user = USERS / mode
    output = OUT / mode
    output.mkdir(exist_ok=True)
    compile_flags = [clang, "--target=wasm32-unknown-unknown", "-ffreestanding", "-O2",
                     "-Wall", "-Wextra", "-Werror", "-pedantic", standard, "-I", include]
    declarations, checks, all_objects = [], [], []
    source_ext, header_ext = suffix
    c_link = 'extern "C" ' if mode == "cpp" else ""
    no_args = "" if mode == "cpp" else "void"
    for header in sorted((include / "uwrosv2").glob("*." + header_ext)):
        domain = header.stem
        source = user / f"domain_{domain}.{source_ext}"
        signature = f"{c_link}void check_{domain}({no_args})"
        lines = [f"#include <uwrosv2/{header.name}>"]
        ops = DOMAINS.get(domain, [])
        if ops:
            lines += ["", signature + " {"]
            for op in ops:
                raw = raw_symbol(op)
                if mode == "cpp":
                    raw = f"uwrosv2::{domain}::raw::{raw}"
                values = ", ".join("0" for _ in op["parameters"])
                denied = "static_cast<uint32_t>(uwrosv2::status::denied)" if mode == "cpp" else "UWROSV2_DENIED"
                lines.append(f"    if ({raw}({values}) != {denied}) __builtin_trap();")
            lines.append("}")
            declarations.append(signature + ";")
            checks.append(f"    check_{domain}();")
        source.write_text("\n".join(lines) + "\n")
        obj = output / f"{domain}.o"
        run(*compile_flags, "-c", source, "-o", obj)
        all_objects.append(obj)
    source = user / f"all.{source_ext}"
    source.write_text("\n".join([*declarations, "", f'{c_link}void _start({no_args}) {{', *checks, "}"]) + "\n")
    obj = output / "all.o"
    run(*compile_flags, "-c", source, "-o", obj)
    run("wasm-ld-21", "--no-entry", "--export=_start", "--fatal-warnings", obj, *all_objects, "-o", output / "all.wasm")
    for name, entry in (("abi", "test_abi"), ("guard", "_start")):
        obj = output / f"guest_{name}.o"
        run(*compile_flags, "-c", user / f"{name}.{source_ext}", "-o", obj)
        run("wasm-ld-21", "--no-entry", f"--export={entry}", "--fatal-warnings", obj, "-o", output / f"{name}.wasm")


def rust_build():
    user = USERS / "rust"
    output = OUT / "rust"
    output.mkdir(exist_ok=True)
    target_flags = ["--sysroot", "/work/rust-sysroot", "--target", "wasm32-unknown-unknown",
                    "--edition", "2021", "-D", "warnings", "-C", "opt-level=2", "-C", "panic=abort"]
    lib = output / "libuwrosv2.rlib"
    run("rustc", *target_flags, "--crate-name", "uwrosv2", "--crate-type", "rlib",
        BINDINGS / "rust/uwrosv2/src/lib.rs", "-o", lib)
    lines = ["#![no_std]", "", "#[panic_handler]",
             "fn panic(_: &core::panic::PanicInfo<'_>) -> ! { core::arch::wasm32::unreachable() }", ""]
    checks = []
    for domain, ops in sorted(DOMAINS.items()):
        lines.append(f"mod domain_{domain};")
        checks.append(f"    domain_{domain}::check();")
        source = user / f"domain_{domain}.rs"
        domain_lines = [f"use uwrosv2::{domain}::ffi;", "", "pub fn check() {", "    unsafe {"]
        for op in ops:
            values = ", ".join("0" for _ in op["parameters"])
            domain_lines += [f"        if ffi::{rust_member(op)}({values}) != uwrosv2::status::DENIED {{",
                             "            core::arch::wasm32::unreachable();", "        }"]
        domain_lines += ["    }", "}"]
        source.write_text("\n".join(domain_lines) + "\n")
    lines += ["", "#[no_mangle]", 'pub extern "C" fn _start() {', *checks, "}"]
    (user / "all.rs").write_text("\n".join(lines) + "\n")
    for name in ("all", "abi", "guard"):
        run("rustc", *target_flags, "--extern", f"uwrosv2={lib}", "--crate-name", f"check_{name}",
            "--crate-type", "cdylib", user / f"{name}.rs", "-o", output / f"{name}.wasm")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    shutil.copytree(Path(__file__).resolve().parent / "fixtures", USERS, dirs_exist_ok=True)
    c_cxx_build("c", "clang-21", "c", ("c", "h"), "-std=c11")
    c_cxx_build("c++", "clang++-21", "cpp", ("cc", "hpp"), "-std=c++17")
    rust_build()
