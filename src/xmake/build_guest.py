"""Build one guest with the compiler selected by the installed Xmake adapter."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

CFAMILY = {"c": ("wrc", "c", (".c",)), "cpp": ("wrcc", "c++", (".cpp", ".cxx", ".cc")),
           "objc": ("wroc", "objc", (".m",)), "objcpp": ("wrocxx", "objc", (".m", ".mm"))}
GO_COMMANDS = {"go": "wrgo", "tinygo": "wrtg"}
SCRIPT_COMMANDS = {"as": "wras", "js": "wrjs", "typescript": "wrts"}


def upstream_rust(args, env):
    if (len(args.sources) != 1 or args.sources[0].suffix != ".rs" or args.mte or args.eh or args.threads
            or args.abi != "wasm32" or args.core != "3.0"):
        raise ValueError("experimental Rust requires one wasm32, no_std, panic-abort crate root with MTE and EH disabled")
    rustc = os.environ.get("WROS_RUSTC", "rustc")
    env.update(RUSTUP_AUTO_INSTALL="0", CARGO_NET_OFFLINE="true")
    common = [rustc, "--target", "wasm32-unknown-unknown", "--edition=2021",
              "-C", "panic=abort", "-C", "opt-level=" + (args.O or "2")]
    if args.g:
        common.append("-g")
    with tempfile.TemporaryDirectory(dir=args.output.parent, prefix="rust-") as directory:
        scratch = Path(directory)
        env["TMPDIR"] = str(scratch)
        libs = [("uwrosv2", args.sdk / "include/u2rosv2/universal/rust/uwrosv2/src/lib.rs")]
        if args.platform != "generic":
            name = "unitree_go2" if args.platform == "unitree" else "wros_observation"
            libs.append((name, args.sdk / "include/u2rosv2/platform" / args.platform / "rust/lib.rs"))
        externs = []
        for name, source in libs:
            archive = scratch / f"lib{name}.rlib"
            subprocess.run([*common, "--crate-name", name, "--crate-type", "rlib", source, "-o", archive],
                           check=True, env=env)
            externs += ["--extern", f"{name}={archive}"]
        result = scratch / "guest.wasm"
        subprocess.run([*common, "--crate-name", "guest", "--crate-type", "cdylib", *externs,
                        args.sources[0], "-o", result], check=True, env=env)
        os.replace(result, args.output)


def script_command(args):
    """Translate the Xmake profile into the selected frontend's actual command line."""
    if args.abi != "wasm32" or args.core != "3.0" or args.threads:
        raise ValueError("the script frontends build single-threaded Core 3 wasm32 guests")
    if args.O not in (None, "3"):
        raise ValueError("the script frontends use their fixed level-3 optimization profiles")
    flags = ["--platform", args.platform, "--target", args.abi, "--mte" if args.mte else "--no-mte"]
    if args.language == "as":
        if len(args.sources) != 1:
            raise ValueError("wras takes one AssemblyScript application source")
        if args.as_driver:
            flags.append("--ros-driver")
        elif args.operation == ["abi"]:
            flags.append("--ros-abi")
        elif args.operation:
            raise ValueError("the scalar AssemblyScript profile supports only the abi import")
        if args.g:
            flags.append("-g")
        sources = args.sources
    else:
        if not args.eh:
            raise ValueError("the embedded QuickJS C backend requires the EH profile")
        sources = [path.resolve() for path in args.sources]
        if args.entry:
            entry = args.entry.resolve()
            if entry not in sources:
                raise ValueError("the script entry must be declared with add_files")
            sources.remove(entry)
            sources.insert(0, entry)
        elif len(sources) != 1:
            raise ValueError("use set_wros_entry to identify the entry in a multi-file script project")
        root = Path(os.path.commonpath([source.parent for source in sources]))
        if args.language == "js":
            flags += ["--entry-name", sources[0].relative_to(root).as_posix()]
            for path in sources[1:]:
                flags += ["--module", path.relative_to(root).as_posix() + "=" + str(path)]
            sources = sources[:1]
        else:
            flags += ["--project-root", str(root)]
    if args.language != "as" or args.as_driver:
        for name in args.operation:
            flags += ["--ros-operation", name]
    return [args.sdk / "bin" / SCRIPT_COMMANDS[args.language], *flags, *sources, "-o", args.output]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sdk", type=Path, required=True)
    p.add_argument("--language", choices=(*CFAMILY, "wat", "rust", "py", "java", *SCRIPT_COMMANDS, *GO_COMMANDS), required=True)
    p.add_argument("--platform", required=True)
    p.add_argument("--abi", choices=("wasm32", "wasm64"), required=True)
    p.add_argument("--core", choices=("mvp", "3.0"), required=True)
    for key in ("eh", "mte", "memory64", "threads"):
        p.add_argument("--" + key, action=argparse.BooleanOptionalAction, required=True)
    p.add_argument("--herbceptions", action=argparse.BooleanOptionalAction)
    p.add_argument("--as-driver", action="store_true")
    p.add_argument("--entry", type=Path)
    p.add_argument("--main-class")
    p.add_argument("--project-root", type=Path)
    p.add_argument("--std")
    p.add_argument("-O", choices=list("0123sz"))
    p.add_argument("-g", action="store_true")
    p.add_argument("--operation", action="append", default=[])
    p.add_argument("--export", action="append", default=[])
    p.add_argument("--link-library", action="append", default=[])
    p.add_argument("-I", action="append", default=[], type=Path)
    p.add_argument("-D", action="append", default=[])
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("sources", nargs="+", type=Path)
    args = p.parse_args()
    selection = json.loads((args.sdk / "selection.json").read_bytes())
    if args.platform != selection["platform"] or args.language != selection["language"]:
        p.error("the requested platform and language must match the installed SDK selection")
    env = dict(os.environ, TMPDIR=str(args.output.parent.resolve()), PYTHONDONTWRITEBYTECODE="1")
    if args.language not in CFAMILY and (args.I or args.D or args.export or args.std or args.link_library):
        p.error("include paths, defines, link exports, libraries and standards require a C-family frontend")
    if args.as_driver and args.language != "as":
        p.error("--as-driver applies to AssemblyScript")
    if args.entry and args.language not in ("js", "typescript", "py"):
        p.error("--entry applies to JavaScript, TypeScript and Python")
    if args.project_root and args.language != "py":
        p.error("--project-root applies to Python application packages")
    if args.main_class and args.language != "java":
        p.error("--main-class applies to Java")
    if args.language == "java":
        if not args.main_class or args.operation:
            p.error("Java requires a main class and resolves scene imports from reachable bindings")
        if args.abi != "wasm32" or args.core != "3.0" or args.threads or not (args.eh and args.mte and args.memory64):
            p.error("Java requires the single-threaded Core 3.0 wasm32 EH/MTE profile")
        flags = ["--main-class", args.main_class, "--platform", args.platform]
        if args.O:
            flags.append("-O" + args.O)
        if args.g:
            flags.append("-g")
        subprocess.run([args.sdk / "bin/wrjava", *flags, "-o", args.output, "--", *args.sources], check=True, env=env)
        return
    if args.language == "py":
        if args.O not in (None, "3"):
            p.error("the published CPython runtime uses the level-3 C compiler profile")
        flags = ["--platform", args.platform, "--target", args.abi, "--core", args.core]
        for name in ("memory64", "eh", "mte", "threads"):
            flags.append(("--" if getattr(args, name) else "--no-") + name)
        if args.g:
            flags.append("-g")
        if args.entry:
            flags += ["--entry", args.entry]
        if args.project_root:
            flags += ["--project-root", args.project_root]
        for name in args.operation:
            flags += ["--ros-operation", name]
        subprocess.run([sys.executable, "-I", "-B", args.sdk / "bin/wrpy.py", *flags,
                        "-o", args.output, "--", *args.sources], env=env, check=True)
        return
    if args.language in GO_COMMANDS:
        if len(args.sources) != 1 or args.sources[0].name != "go.mod" or not args.sources[0].is_file():
            p.error("declare the Go application module with add_files(\"go.mod\")")
        if args.operation:
            p.error("Go imports are selected by reachable //go:wasmimport declarations")
        flags = ["--platform", args.platform, "--target", args.abi, "--core", args.core]
        for key in ("memory64", "eh", "mte", "threads"):
            flags.append(("--" if getattr(args, key) else "--no-") + key)
        if args.O:
            flags.append("-O" + args.O)
        if args.g:
            flags.append("-g")
        subprocess.run([args.sdk / "bin" / GO_COMMANDS[args.language], *flags, args.sources[0].parent,
                        "-o", args.output], env=env, check=True)
        return
    if args.language in SCRIPT_COMMANDS:
        subprocess.run(script_command(args), env=env, check=True)
        return
    if args.language == "rust":
        if selection["mode"] == "bindings":
            return upstream_rust(args, env)
        if len(args.sources) != 1 or args.sources[0].suffix != ".rs":
            p.error("native wrrs takes one Rust crate root; declare its modules with mod")
        flags = ["--platform", args.platform, "--target", args.abi, "--core", args.core]
        for key in ("memory64", "eh", "mte", "threads"):
            flags.append(("--" if getattr(args, key) else "--no-") + key)
        if args.O:
            flags.append("-O" + args.O)
        if args.g:
            flags.append("-g")
        subprocess.run([args.sdk / "bin/wrrs", *flags, args.sources[0], "-o", args.output], env=env, check=True)
        return
    flags = ["--core", args.core, "--mte" if args.mte else "--no-mte", "--eh" if args.eh else "--no-eh"]
    if args.g:
        flags.append("-g")
    if args.language == "wat":
        if len(args.sources) != 1 or args.sources[0].suffix != ".wat" or args.O:
            p.error("wrwat takes one WAT source and does not optimize it")
        program = "wrwat"
        # WAT describes the memory instructions itself. This wrwat option gates the memory64 grammar.
        flags += ["--target", "wasm64" if args.memory64 else "wasm32"]
        if args.threads:
            flags.append("--threads")
        for operation in args.operation:
            flags += ["--ros-operation", operation]
    else:
        program, includedir, suffixes = CFAMILY[args.language]
        if any(source.suffix not in suffixes for source in args.sources):
            p.error("input extension does not match the selected C/C++ driver")
        flags += ["--target", args.abi, "--memory64" if args.memory64 else "--no-memory64",
                  "--reactor", "--export", "_start",
                  "-I", str(args.sdk / "include/u2rosv2/universal" / includedir)]
        if args.platform != "generic":
            flags += ["-I", str(args.sdk / "include/u2rosv2/platform" / args.platform / includedir)]
        if args.threads:
            flags.append("--threads")
        if args.std:
            flags += ["--std", args.std]
        if args.herbceptions is not None:
            flags.append("--herbceptions" if args.herbceptions else "--no-herbceptions")
        if args.O:
            flags.append("-O" + args.O)
        for key, values in (("-I", args.I), ("-D", args.D), ("--export", args.export),
                            ("--link-library", args.link_library)):
            for value in values:
                flags += [key, str(value)]
    subprocess.run([args.sdk / "bin" / program, *flags, *args.sources, "-o", args.output], env=env, check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"Guest build failed: {error}")
