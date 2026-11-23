#!/usr/bin/env python3
"""@file wrts
@brief Type-check TypeScript and compile the application and interpreter into one Wasm module."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk_layout import CONTRACT, ROOT, include_root, selected_platform
HERE = Path(__file__).resolve().parent
RELEASE = "1581ad9a53c0c2e95847b9ab4d4b576dedc4d0d1db2c3ad5e5e8fe0f89e038bc"
SOURCE_LIMIT = 1024 * 1024


def digest(path):
    """@brief Hash the exact bytes of a build input or output."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def compiler(stage):
    """@brief Verify and unpack the registered compiler into a private build directory.
    @return Paths to the TypeScript library and its build-host executable.
    """
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise ValueError("the bundled TypeScript build host requires Linux x86-64")
    manifest = HERE / "release.json"
    if digest(manifest) != RELEASE:
        raise ValueError("unrecognized TypeScript release")
    inputs = json.loads(manifest.read_bytes())
    bundled_node = ROOT / "share/toolchains/node/bin/node"
    default_node = str(bundled_node) if bundled_node.is_file() or (ROOT / "selection.json").is_file() else "node"
    node = shutil.which(os.environ.get("WROS_NODE", default_node))
    if not node or digest(Path(node)) != inputs["node_binary_sha256"]:
        raise ValueError("set WROS_NODE to the pinned Linux x64 Node.js 22.22.3 executable")
    directory = stage / "compiler"
    directory.mkdir()
    for name, expected in inputs["files"].items():
        source = HERE / "compiler" / name
        target = directory / name
        shutil.copyfile(source, target)
        if digest(target) != expected:
            raise ValueError("unexpected TypeScript compiler input: " + name)
    return directory, str(Path(node).resolve())


def sdk_declarations(operations):
    """@brief Declare only the selected, registered ROSv2 methods for strict type checking."""
    catalog = json.loads(CONTRACT.read_bytes())
    published = {row["name"] for row in catalog["operations"]}
    if unknown := set(operations) - published:
        raise ValueError("unknown ROSv2 operations: " + ", ".join(sorted(unknown)))
    methods = {"abi": "abi(): number", "capability.open": "open(alias: string): WrosCapability | number",
               "capability.close": "close(handle: WrosCapability): number"}
    body = ["interface WrosCapability { readonly __wrosCapability: unique symbol }",
            "interface WrosReply { readonly status: number; readonly written: bigint; readonly data: ArrayBuffer | null }",
            "declare const wros: {"]
    for op in operations:
        body.append("  " + methods.get(op, json.dumps(op) +
                    "(handle: WrosCapability | null, input: ArrayBuffer, capacity: number): WrosReply") + ";")
    return "\n".join([*body, "};", ""])


def sdk_modules(operations, platform):
    include = include_root("typescript")
    public = include / "universal/typescript/uwrosv2"
    selected = {"wr_" + name.replace(".", "_") for name in operations}
    modules = {"uwrosv2": public.with_suffix(".d.ts").read_text()}
    for path in sorted(public.glob("*.d.ts")):
        domain = path.name.removesuffix(".d.ts")
        text = path.read_text()
        if domain not in ("memory", "status"):
            declarations = re.findall(r"^export declare function (\w+)([^\n]+);$", text, re.M)
            text = "\n".join("export declare function " + name + signature + ";"
                             for name, signature in declarations if name in selected) or "export {};"
        modules["uwrosv2/" + domain] = text
    if platform != "generic":
        adapter = include / "platform" / platform / "typescript"
        for path in sorted(adapter.rglob("*.d.ts")):
            name = path.relative_to(adapter).as_posix().removesuffix(".d.ts")
            modules[f"uwrosv2/platform/{platform}/{name}"] = path.read_text()
    return modules


def project(args):
    """@brief Snapshot uniquely named UTF-8 source files inside the selected root.
    @return Ordered virtual source files and per-file SHA-256 identities.
    """
    if not 1 <= len(args.sources) <= 128:
        raise ValueError("supply an entry and up to 127 project dependencies")
    root = (args.project_root or args.sources[0].parent).resolve(strict=True)
    remaining = SOURCE_LIMIT
    files, hashes = [], {}
    for source in args.sources:
        path = source.resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file() or path.suffix != ".ts" or path.name.endswith(".d.ts"):
            raise ValueError("expected a project-local .ts implementation: " + str(source))
        name = path.relative_to(root).as_posix()
        if "\\" in name or name in hashes:
            raise ValueError("duplicate or ambiguous TypeScript module: " + name)
        with path.open("rb") as stream:
            data = stream.read(remaining + 1)
        remaining -= len(data)
        if remaining < 0 or b"\x00" in data:
            raise ValueError("expected up to 1 MiB of UTF-8 TypeScript")
        files.append({"name": name, "source": data.decode("utf-8-sig")})
        hashes[name] = hashlib.sha256(data).hexdigest()
    return files, hashes


def main():
    """@brief Publish the guest after type checking, linking and import verification."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sources", type=Path, nargs="+", help="entry first, then all imported .ts files")
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("--platform", help="platform ID (default: installed selection or generic)")
    p.add_argument("--project-root", type=Path, help="common module root (default: entry directory)")
    p.add_argument("--target", choices=["wasm32"], default="wasm32")
    p.add_argument("--mte", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--ros-operation", action="append", default=[])
    p.add_argument("--ros-abi", action="store_true")
    p.add_argument("--toolchain", type=Path)
    p.add_argument("--sysroots", type=Path, action="append", default=[])
    p.add_argument("--require-qualified", action="store_true")
    p.add_argument("--build-receipt", action="store_true")
    args = p.parse_args()
    platform_name = selected_platform(args.platform)
    files, hashes = project(args)
    if args.output.suffix != ".wasm":
        raise ValueError("choose a .wasm output")
    operations = sorted(set(args.ros_operation) | ({"abi"} if args.ros_abi else set()))
    declarations = sdk_declarations(operations)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as work:
        stage = Path(work).resolve()
        directory, node = compiler(stage)
        request = stage / "project.json"
        request.write_text(json.dumps(dict(sources=files, entry=files[0]["name"], declarations=declarations,
                                           sdkModules=sdk_modules(operations, platform_name))))
        emitted, wasm = stage / "modules.json", stage / "application.wasm"
        driver = HERE / "compile.cjs"
        subprocess.run([node, "--jitless", "--single-threaded", "--no-addons", "--max-old-space-size=256",
                        driver, directory, request, emitted], cwd=stage, env={"LANG": "C", "TZ": "UTC", "TMPDIR": str(stage)},
                       check=True, timeout=90)
        output = json.loads(emitted.read_bytes())
        entry = output["entry"]
        expected = {str(Path(name).with_suffix(".js")) for name in hashes}
        if set(output["modules"]) != expected or entry != str(Path(files[0]["name"]).with_suffix(".js")):
            raise ValueError("TypeScript emitted an unexpected module graph")
        paths = {}
        for name, text in output["modules"].items():
            path = stage / "emitted" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            paths[name] = path
        script = paths[entry]
        args_js = [sys.executable, "-B", HERE.parent / "js/driver.py", script, "--entry-name", entry, "-o", wasm,
                   "--target", args.target, "--platform", platform_name, "--mte" if args.mte else "--no-mte", "--build-receipt"]
        for name, path in paths.items():
            if name != entry:
                args_js.extend(["--module", name + "=" + str(path)])
        if args.require_qualified:
            args_js.append("--require-qualified")
        if args.toolchain:
            args_js.extend(["--toolchain", args.toolchain])
        for receipt in args.sysroots:
            args_js.extend(["--sysroots", receipt])
        for op in operations:
            args_js.extend(["--ros-operation", op])
        subprocess.run(args_js, check=True)
        if args.build_receipt:
            backend = Path(str(wasm) + ".wros-js.json")
            js = json.loads(backend.read_bytes())
            if (digest(script) != js["script_sha256"] or digest(wasm) != js["wasm_sha256"] or js["operations"] != operations
                    or any(js["modules"].get(name) != digest(path) for name, path in paths.items())):
                raise ValueError("TypeScript and JavaScript receipts disagree")
            note = dict(language="typescript", compiler_release_sha256=RELEASE, compiler="TypeScript 5.9.3",
                        compiler_driver_sha256=digest(driver), target="ES2022", strict=True,
                        modules="ES2022", entry=files[0]["name"], inputs=hashes, operations=operations,
                        javascript_sha256=digest(script), emitted_modules={name: digest(path) for name, path in paths.items()}, interpreter_receipt_sha256=digest(backend),
                        wasm_sha256=js["wasm_sha256"])
            (stage / "note").write_text(json.dumps(note, indent=2) + "\n")
            os.replace(stage / "note", str(args.output) + ".wros-ts.json")
            for suffix in (".wros-build.json", ".wros-js.json"):
                os.replace(str(wasm) + suffix, str(args.output) + suffix)
        os.replace(wasm, args.output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit("wrts: " + str(error))
