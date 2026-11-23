"""Compile each translation unit with native Wasm Clang and publish the checked result."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[3]
sys.path[:0] = [str(SDK / "install"), str(HERE)]
import artifacts
from compiler import digest, make_command
from frontend import audit, shared_memory_link_flags, sysroot_link_flags
from guest_profile import Profile
from portable_cc import prepare
from runtime import PUBLIC_INCLUDE, objc_flags, runtime_lock, verified_runtime


def compile_native(channel, command):
    packet = b"\0".join([b"embedded", os.fsencode(command[0]), b"-no-canonical-prefixes",
                         *map(os.fsencode, command[1:])]) + b"\0"
    if len(packet) > 8 * 1024 * 1024:
        raise ValueError("native compilation command exceeds the SDK bound")
    channel.sendall(struct.pack("!I", len(packet)) + packet)
    with channel.makefile("rb") as stream:
        result = stream.read(4)
    if len(result) != 4:
        raise ValueError("native Clang did not report its result")
    code, = struct.unpack("!I", result)
    if code:
        raise subprocess.CalledProcessError(code, command)


def main(language, descriptor, arguments):
    cpp = language == "objcpp"
    parser = argparse.ArgumentParser(prog="wrocxx" if cpp else "wroc", description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--platform", choices=["generic"], default="generic")
    parser.add_argument("--target", choices=["wasm32", "wasm64"], default="wasm32")
    parser.add_argument("--core", choices=["3.0"], default="3.0")
    for key, default in [("eh", True), ("mte", True), ("memory64", True), ("threads", False)]:
        parser.add_argument("--" + key, action=argparse.BooleanOptionalAction, default=default)
    parser.add_argument("--shared-memory-pages", type=int, metavar="MAX")
    model = parser.add_mutually_exclusive_group()
    model.add_argument("--reactor", action="store_true")
    model.add_argument("--wasi-reactor", action="store_true")
    parser.add_argument("-l", "--link-library", dest="libraries", action="append", default=[])
    parser.add_argument("--export", action="append", default=[])
    parser.add_argument("-I", dest="includes", action="append", type=Path, default=[])
    parser.add_argument("-D", dest="defines", action="append", default=[])
    parser.add_argument("--std", choices=["c++98", "c++03", "c++11", "c++14", "c++17", "c++20", "c++23", "c++26"] if cpp
                        else ["c11", "c17", "c23"])
    parser.add_argument("-O", choices=list("0123sz"), default="2")
    parser.add_argument("-g", action="store_true")
    parser.add_argument("-c", "--compile-only", action="store_true")
    args = parser.parse_args(arguments)
    if language not in ("objc", "objcpp"):
        parser.error("unknown frontend")
    selection = json.loads((SDK / "selection.json").read_bytes())
    if selection["language"] != language or selection["platform"] != args.platform:
        parser.error("language or platform differs from the installed selection")
    if args.compile_only and args.shared_memory_pages is not None:
        parser.error("--shared-memory-pages requires a final link")
    profile = Profile(int(args.target[4:]), args.core, args.threads, args.mte, "eh" if args.eh else "noeh")
    profile.memory64_enabled(args.memory64)
    library_flags = sysroot_link_flags(args.libraries, args.compile_only)
    dialects = {".m": "objective-c"}
    if cpp:
        dialects.update({".mm": "objective-c++", ".cc": "c++", ".cpp": "c++",
                         ".cxx": "c++", ".C": "c++"})
    sources = [source.resolve(strict=True) for source in args.sources]
    if len(sources) > artifacts.MAX_MEMBERS:
        parser.error("too many compiler inputs")
    if any(p.suffix not in dialects and p.suffix not in (".o", ".a") for p in sources):
        parser.error("expected source (" + ", ".join(dialects) + ") or a matching SDK object/archive")
    if args.compile_only and (len(sources) != 1 or sources[0].suffix not in dialects or args.export or args.reactor or args.wasi_reactor):
        parser.error("-c takes one translation unit and no link options")
    if args.output.resolve() in sources:
        parser.error("output aliases a build input")
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name, re.ASCII) for name in args.export):
        parser.error("invalid Wasm export name")
    if any(not re.fullmatch(r"[A-Za-z_]\w*(?:=[^\0\r\n]*)?", name, re.ASCII) for name in args.defines):
        parser.error("invalid preprocessor definition")
    if any(not path.is_dir() for path in args.includes):
        parser.error("include path is not a directory")

    tools, sysroot = prepare(SDK, language="cpp", profile=profile)
    # clang++ supplies the C++ link libraries for libobjc2 in both frontends.
    # The source language for each cc1 job is selected explicitly below.
    base, record = make_command(tools, [sysroot], profile, "cpp", [], verify=True)
    if digest(Path("/proc") / str(os.getppid()) / "exe") != record["compiler_sha256"]:
        raise ValueError("the running Objective-C compiler differs from its installed receipt")
    common = [flag for flag in base if flag != "-lunwind"]
    compile_flags = ["-O" + args.O]
    if args.g:
        compile_flags.append("-g")
    directories = [SDK / PUBLIC_INCLUDE, SDK / "include/u2rosv2/universal/objc",
                   SDK / "include/u2rosv2/universal/c", *args.includes]
    compile_flags.extend("-I" + str(directory.resolve()) for directory in directories)
    compile_flags.extend("-D" + name for name in args.defines)
    link_flags = shared_memory_link_flags(profile, args.shared_memory_pages, wasi_crt=not args.reactor)
    if args.reactor:
        link_flags.extend(["-nostartfiles", "-Wl,--no-entry"])
    if args.wasi_reactor:
        link_flags.append("-mexec-model=reactor")
    link_flags.extend("-Wl,--export=" + name for name in args.export)
    with (socket.socket(fileno=descriptor) as channel, runtime_lock(SDK, profile),
          tempfile.TemporaryDirectory(dir=args.output.resolve().parent) as temporary):
        runtime, language_closure = verified_runtime(SDK, profile, record)
        work = Path(temporary)
        inputs = artifacts.stage_inputs(sources, work, profile.to_dict(), record["compiler_sha256"],
                                        language_closure, tools)
        result = work / ("guest.o" if args.compile_only else "guest.wasm")
        for index, source in enumerate(inputs):
            dialect = dialects.get(source.suffix)
            if dialect is None:
                continue
            command = [*common, *compile_flags]
            if dialect != "c++":
                command.extend(objc_flags(profile))
            if args.std and (not cpp or dialect != "objective-c"):
                command.append("-std=" + args.std)
            obj = result if args.compile_only else work / f"unit{index}.o"
            compile_native(channel, [*command, "-x", dialect, "-c", source, "-o", obj])
            inputs[index] = obj
        if not args.compile_only:
            command = [*common, *link_flags, *inputs, runtime / "libuwrosobjc.a",
                       runtime / "libobjc.a", *library_flags]
            if profile.exceptions == "eh":
                command.append("-lunwind")
            compile_native(channel, [*command, "-o", result])
        data = artifacts.read_bounded(result)
        if args.compile_only:
            data = artifacts.seal_object(data, profile.to_dict(), record["compiler_sha256"], language_closure)
        else:
            data = artifacts.strip_notes(data)
            audit(data, profile, args.shared_memory_pages, memory64=args.memory64)
        result.write_bytes(data)
        os.replace(result, args.output)


if __name__ == "__main__":
    try:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3:])
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
