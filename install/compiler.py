"""Resolve verified Wasm compiler and sysroot inputs for the SDK frontends."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shlex


def compiler_environment(toolchain):
    """Run the explicit compiler without ambient driver overrides or search paths."""
    environment = {"PATH": str(toolchain.resolve() / "bin") + os.pathsep + os.defpath,
                   "LC_ALL": "C", "TZ": "UTC"}
    for key in ("TMPDIR", "SOURCE_DATE_EPOCH"):
        if key in os.environ:
            environment[key] = os.environ[key]
    return environment


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def confined(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("build receipt contains an unconfined path: " + relative)
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("build receipt symlink escapes its root: " + relative)
    return result


def expand_responses(arguments, cwd=None):
    """Expand Clang's Linux response syntax within fixed byte/depth/work limits.

    No shell evaluation occurs. Repeated acyclic includes count again against
    the limits, so an exponentially expanding response graph also refuses.
    """
    cwd = Path.cwd() if cwd is None else cwd
    result, active = [], set()
    consumed, visited = 0, 0
    stack = [(iter(arguments), None)]
    while stack:
        iterator, path = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            if path is not None:
                active.remove(path)
            continue
        visited += 1
        if visited > 65536:
            raise ValueError("compiler response expansion exceeds argument bound")
        if item.startswith("@"):
            path = (cwd / item[1:]).resolve()
            if path in active:
                raise ValueError("cyclic compiler response file: " + str(path))
            if len(stack) >= 16:
                raise ValueError("compiler response nesting exceeds depth bound")
            with path.open("rb") as stream:
                data = stream.read(8 * 1024 * 1024 - consumed + 1)
            consumed += len(data)
            if consumed > 8 * 1024 * 1024:
                raise ValueError("compiler response expansion exceeds byte bound")
            active.add(path)
            stack.append((iter(shlex.split(data.decode("utf-8"), comments=False, posix=True)), path))
        else:
            result.append(item)
    return result


def select_closure(receipts, profile, compiler_sha256):
    found = []
    for filename in receipts:
        filename = filename.resolve()
        value = json.loads(filename.read_text())
        if value.get("schema") != "uwvm-memtag-sysroot-build-v1" or value.get("status") != "built-awaiting-qualification":
            raise ValueError("not a completed stable sysroot build receipt: " + str(filename))
        if value.get("compiler_sha256") != compiler_sha256:
            # Another compiler version's closure is not a usable fallback.
            continue
        for target in value["targets"]:
            if target.get("guest_profile") == profile.to_dict():
                if not profile.mte and not value.get("producer_mte_codegen", {}).get(str(profile.address_bits)):
                    raise ValueError("sysroot lacks verified WasmMTE compiler capability for this width")
                root = confined(filename.parent, target["sysroot"])
                resource = confined(filename.parent, target["resource"])
                if not (root / "include" / profile.triple / "stdio.h").is_file() or not (resource / "include/stddef.h").is_file():
                    raise ValueError("sysroot/resource headers missing: " + str(filename))
                for library in ("libc.a", "libc++.a", "libc++abi.a", "crt1.o"):
                    if not (root / "lib" / profile.triple / library).is_file():
                        raise ValueError("incomplete sysroot: " + library)
                if profile.exceptions == "eh" and not (root / "lib" / profile.triple / "libunwind.a").is_file():
                    raise ValueError("exception profile lacks libunwind")
                found.append((filename, value, target, root, resource))
    if not found:
        raise ValueError("no sysroot built by this compiler for " + profile.identity + "; build that exact profile; no downgrade or host-library fallback is performed")
    if len(found) != 1:
        raise ValueError("ambiguous sysroot receipts for " + profile.identity + "; select exactly one")
    return found[0]


def make_command(toolchain, receipts, profile, language, arguments, verify=False):
    if language not in ("c", "cpp"):
        raise ValueError("this driver handles c/cpp; other languages need their own complete MTE runtime closure")
    toolchain = toolchain.resolve()
    compiler = toolchain / "bin" / ("clang++" if language == "cpp" else "clang")
    linker = toolchain / "bin/wasm-ld"
    if not compiler.is_file() or not linker.is_file():
        raise ValueError("explicit stable compiler/linker prefix is incomplete")
    argv = expand_responses(arguments)
    for item in argv:
        if item in ("-target", "--target", "--sysroot", "-isysroot", "-resource-dir", "-m32", "-m64", "-pthread", "-fwasm-exceptions", "-fexceptions", "-fno-exceptions") or item.startswith(("--target=", "-target=", "--sysroot=", "-isysroot", "-resource-dir=", "-fuse-ld=", "-fsanitize=", "-fno-sanitize=")):
            raise ValueError("use the SDK profile options instead of overriding " + item)
    filename, value, target, root, resource = select_closure(receipts, profile, digest(compiler))
    if verify:
        builtin_dir = resource / "lib" / profile.triple.replace("-wasip1", "-unknown-wasip1")
        roots = (root, resource / "include", builtin_dir)
        recorded = target["files"]
        for directory in roots:
            for file in directory.rglob("*"):
                if file.is_file() and str(file.relative_to(filename.parent)) not in recorded:
                    raise ValueError("unrecorded sysroot input: " + str(file))
        builtin = str((builtin_dir / "libclang_rt.builtins.a").relative_to(filename.parent))
        if builtin not in recorded or recorded[builtin] != target["builtins_sha256"]:
            raise ValueError("compiler-rt does not match the selected target")
        for relative, expected in target["files"].items():
            path = confined(filename.parent, relative)
            if digest(path) != expected:
                raise ValueError("sysroot file hash mismatch: " + relative)
    flags = ["--no-default-config", "--target=" + profile.triple, "--sysroot=" + str(root),
             "-resource-dir=" + str(resource), "-fuse-ld=" + str(linker),
             *profile.llvm_feature_flags()]
    flags += ["-fsanitize=memtag" if profile.mte else "-fno-sanitize=memtag"]
    if profile.exceptions == "eh":
        flags += ["-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false"]
    elif language == "cpp":
        flags += ["-fno-exceptions"]
    # Static archive order is meaningful: put libunwind after caller inputs.
    command = [str(compiler), *flags, *argv]
    if profile.exceptions == "eh" and not any(x in argv for x in ("-c", "-S", "-E", "-fsyntax-only")):
        command += ["-lunwind"]
    closure = hashlib.sha256(json.dumps(target, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return command, dict(closure_sha256=closure, profile=profile.to_dict(), receipt=str(filename),
                         compiler_sha256=value["compiler_sha256"],
                         qualified=bool(target.get("qualified", False)), authority_grants=[])


if __name__ == "__main__":
    raise SystemExit("Build Wasm applications with bin/wrc or bin/wrcc.")
