#!/usr/bin/env python3
"""Compile an embedded JavaScript application and its QuickJS interpreter to one core Wasm module."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk_layout import ROOT, CONTRACT, include_root, native, selected_platform
HERE = Path(__file__).resolve().parent
from artifacts import read_bounded
from imports import inspect

UNITS = ("quickjs", "libregexp", "libunicode", "cutils", "dtoa")
SPECIAL = {"abi": ([], "ABI"), "capability.open": (["i32", "i64", "i64", "i64"], "OPEN"),
           "capability.close": (["i64"], "CLOSE")}
COMMON_ARGS = ["i64", "i32", "i64", "i64", "i64", "i64", "i64"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def selection(names):
    catalog = json.loads(CONTRACT.read_bytes())
    signatures = {row["name"]: row["wasm_signature"] for row in catalog["operations"]}
    flags, methods, adapters, raw = [], [], [], []
    for name in sorted(names):
        if name not in signatures or not re.fullmatch(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*", name):
            raise ValueError("unknown ROSv2 operation: " + name)
        params = SPECIAL[name][0] if name in SPECIAL else COMMON_ARGS
        if signatures[name] != {"parameters": params, "results": ["i32"]}:
            raise ValueError("unsupported operation signature: " + name)
        symbol = "uwrosv2_raw_" + name.replace(".", "_")
        adapter = "call_" + name.replace(".", "_")
        arguments = ", ".join(f"(uint{ty[1:]}_t)args[{i}]" for i, ty in enumerate(params))
        adapters.append(f"static uint32_t {adapter}(const uint64_t *args) {{ (void)args; return {symbol}({arguments}); }}")
        mask = sum((ty == "i64") << i for i, ty in enumerate(params))
        raw.append(f'    {{"{name}", {len(params)}, {mask}, {adapter}}},')
        if name in SPECIAL:
            flags.append("#define WROS_JS_" + SPECIAL[name][1] + " 1")
        else:
            partial = int(name in ("permission.report", "module.permission.report"))
            methods.append('    {"%s", uwrosv2_raw_%s, %d},' % (name, name.replace(".", "_"), partial))
    return "\n".join([*flags, *adapters, "static const RawMethod raw_methods[] = {", *raw,
                      "    {NULL, 0, 0, NULL}", "};", "static const Method methods[] = {",
                      *methods, "    {NULL, NULL, 0}", "};", ""])


def literal(data):
    return "\n".join('"' + "".join("\\%03o" % value for value in data[i:i+128]) + '"'
                     for i in range(0, len(data), 128)) or '""'


def project_name(name):
    path = PurePosixPath(name)
    return (path.suffix in (".js", ".mjs") and not path.is_absolute() and ".." not in path.parts
            and str(path) == name and not name.startswith("uwrosv2/") and "\\" not in name
            and not any(ord(c) < 32 for c in name))


def bundle(entry, entry_name, specs, platform):
    if not project_name(entry_name):
        raise ValueError("invalid project entry module name")
    include = include_root("js")
    public = include / "universal/js/uwrosv2"
    entries = {"uwrosv2": public.with_suffix(".mjs"),
               **{"uwrosv2/" + path.stem: path for path in sorted(public.glob("*.mjs"))}}
    if platform != "generic":
        adapter = include / "platform" / platform / "js"
        for path in sorted(adapter.rglob("*.mjs")):
            name = path.relative_to(adapter).with_suffix("").as_posix()
            entries[f"uwrosv2/platform/{platform}/{name}"] = path
        if platform != "unitree":
            entries["uwrosv2/shared/reader.mjs"] = include / "platform/shared/reader.mjs"
    public_count = len(entries)
    for spec in specs:
        name, separator, path = spec.partition("=")
        if (not separator or not project_name(name)
                or name in entries or name == entry_name or len(entries) - public_count >= 127):
            raise ValueError("expected a unique project module name=path")
        entries[name] = Path(path)
    sources, total = {}, 0
    for name, path in [(entry_name, entry), *entries.items()]:
        with path.open("rb") as stream:
            data = stream.read(1024 * 1024 + 1)
        total += len(data)
        if len(data) > 1024 * 1024 or total > 4 * 1024 * 1024 or b"\x00" in data:
            raise ValueError("expected UTF-8 modules up to 1 MiB each and 4 MiB total")
        data.decode("utf-8")
        sources[name] = data
    rows = [f"static const char application[] = {literal(sources[entry_name])};",
            f"static const char application_name[] = {literal(entry_name.encode())};",
            f"static const int application_is_module = {int(entry.suffix == '.mjs')};",
            "static const struct { const char *name, *source; size_t length; } modules[] = {"]
    for name in entries:
        rows.append("    {" + literal(name.encode()) + ", " + literal(sources[name]) +
                    ", " + str(len(sources[name])) + "},")
    return "\n".join([*rows, "};", ""]), {name: sha(data) for name, data in sources.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--entry-name", help="project-relative virtual module name (default: entry basename)")
    parser.add_argument("--platform", help="platform ID (default: installed selection or generic)")
    parser.add_argument("--module", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--require-qualified", action="store_true")
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--target", choices=["wasm32"], default="wasm32")
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--sysroots", type=Path, action="append")
    parser.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ros-operation", action="append", default=[])
    parser.add_argument("--ros-abi", action="store_true", help="include wros.abi()")
    parser.add_argument("--build-receipt", action="store_true")
    args = parser.parse_args()
    operations = set(args.ros_operation)
    if args.ros_abi:
        operations.add("abi")
    methods = selection(operations)
    if args.output.suffix != ".wasm" or args.script.resolve() == args.output.resolve():
        raise ValueError("choose a distinct .wasm output")
    if args.script.name == "uwrosv2" or args.script.suffix not in (".js", ".mjs"):
        raise ValueError("choose a .js or .mjs application")
    entry_name = args.entry_name or args.script.name
    application, hashes = bundle(args.script, entry_name, args.module, selected_platform(args.platform))
    # The pinned installation verifies these files. Snapshot the bytes used by
    # this particular build and bind them to the optional application receipt.
    source = HERE / "quickjs"
    with tempfile.TemporaryDirectory(dir=args.output.parent) as scratch:
        stage = Path(scratch).resolve()
        inputs = {}
        with (source / "official-source.json").open("rb") as stream:
            release = stream.read(4097)
        if sha(release) != "98a8ca8ccd0817b1528904f978c16f7b3698e9cdf03c6cc5b6e22727965dde76":
            raise ValueError("unexpected QuickJS official release manifest")
        manifest = json.loads(release)
        engine_files = {name for name in manifest["files"] if name.endswith((".h", ".c"))}
        paths = [*sorted(source.glob("*.h")), *[source / (n + ".c") for n in UNITS]]
        if {path.name for path in paths} != engine_files:
            raise ValueError("unexpected QuickJS release source inventory")
        for path in [HERE / "entry.c", *paths]:
            data = read_bounded(path)
            digest = sha(data)
            if path.parent == source and digest != manifest["files"][path.name]["sdk_sha256"]:
                raise ValueError("QuickJS source differs from the reviewed official release adaptation: " + path.name)
            inputs[path.relative_to(ROOT).as_posix()] = digest
            (stage / path.name).write_bytes(data)
        (stage / "application.inc").write_text(application)
        (stage / "operations.inc").write_text(methods)
        wasm = stage / "body.wasm"
        cmd = [native("wrc"), "--target", "wasm32", "--core", "3.0", "--eh", "-O3", "-g",
               "--mte" if args.mte else "--no-mte", "--reactor", "--export", "_start", "--build-receipt",
               "-I", stage, "-I", include_root("c") / "universal/c", "-D", 'CONFIG_VERSION="2026-06-04"', "-D", "_GNU_SOURCE"]
        if args.require_qualified:
            cmd.append("--require-qualified")
        if args.toolchain:
            cmd.extend(["--toolchain", args.toolchain])
        for receipt in args.sysroots or []:
            cmd.extend(["--sysroots", receipt])
        cmd.extend([*[stage / (n + ".c") for n in UNITS], stage / "entry.c", "-o", wasm])
        subprocess.run(cmd, env=dict(os.environ, TMPDIR=str(stage)), check=True)
        data = read_bounded(wasm)
        actual = {(i["module"], i["name"]) for i in inspect(data)}
        expected = {("uwvm_ros_v2", name) for name in operations} | {("wasi_snapshot_preview1", "clock_time_get")}
        if actual != expected:
            raise ValueError("unexpected final QuickJS imports: " + repr(sorted(actual)))
        backend = Path(str(wasm) + ".wros-build.json")
        body = backend.read_bytes()
        evidence = json.loads(body)
        if (evidence.get("artifact_sha256") != sha(data) or evidence["profile"]["mte"] != args.mte or
                args.require_qualified and evidence.get("mode") != "strict"):
            raise ValueError("interpreter module and C compiler receipt disagree")
        if args.build_receipt:
            note = stage / "javascript.json"
            note.write_text(json.dumps(dict(language="js", interpreter="QuickJS", script_sha256=hashes[entry_name], modules=hashes,
                sources=inputs, operations=sorted(operations), wasm_sha256=sha(data), backend_build_sha256=sha(body)),
                indent=2) + "\n")
            os.replace(note, str(args.output) + ".wros-js.json")
            os.replace(backend, str(args.output) + ".wros-build.json")
        os.replace(wasm, args.output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit("wrjs: " + str(error))
