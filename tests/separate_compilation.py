"""Compile real MTE Wasm objects/archives and exercise both VM execution engines.

Run through the repository's existing 64 GiB cgroup gate. Receipts are scoped
to the exact local compiler, sysroot, installed frontend and runtime hashes;
they do not qualify another language, vendor, or deployment environment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import os
import resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import check_object, read_bounded
from guest_profile import Profile
from imports import inspect


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cgroup_record():
    """Refuse execution without the required 64 GiB, zero-swap ancestor."""
    entry = next((line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::")), None)
    if entry is None:
        raise RuntimeError("a cgroup v2 execution gate is required")
    root = Path("/sys/fs/cgroup")
    current = root / entry.lstrip("/")
    for group in (current, *current.parents):
        if not group.is_relative_to(root):
            break
        if ((group / "memory.max").is_file() and
                (group / "memory.max").read_text().strip() == "68719476736" and
                (group / "memory.swap.max").read_text().strip() == "0"):
            return dict(path=str(group), memory_max=68719476736, swap_max=0)
    raise RuntimeError("no visible 64 GiB zero-swap ancestor; use the repository gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("frontend-root", "toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    options = parser.parse_args()
    controller = cgroup_record()
    front, toolchain, receipt, runtime, work = [getattr(options, name).resolve() for name in
        ("frontend_root", "toolchain", "sysroots", "runtime", "output")]
    work.mkdir(parents=True, exist_ok=False)
    (work / "tmp").mkdir()
    os.environ["TMPDIR"] = str(work / "tmp")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    paths = [Path(__file__).resolve(), receipt, runtime, toolchain / "bin/clang", toolchain / "bin/wasm-ld",
             toolchain / "bin/llvm-ar", front / "share/abi/ros.json"]
    paths += sorted((front / "install").glob("*.py")) + sorted((front / "bin").glob("wr*"))
    hashes = {str(p): sha(p) for p in paths}
    result = dict(complete=False, cgroup=controller, inputs=hashes, cases=[], artifacts={})

    def save():
        (work / "results.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(label, argv, ok=True, error=None):
        cmd = list(map(str, argv))
        proc = subprocess.run(cmd, cwd=work, capture_output=True, timeout=120)
        (work / (label + ".stdout")).write_bytes(proc.stdout)
        (work / (label + ".stderr")).write_bytes(proc.stderr)
        result["cases"].append(dict(label=label, argv=cmd, exit=proc.returncode, expected_success=ok))
        save()
        if (proc.returncode == 0) != ok or (error and error.encode() not in proc.stderr):
            raise RuntimeError(label + ": " + proc.stderr.decode(errors="replace")[-4000:])
        print(label, proc.returncode, flush=True)

    def compile_cmd(bits, language="cpp", *extra):
        return [front / "bin" / ("wrc" if language == "c" else "wrcc"), "--toolchain", toolchain,
                "--sysroots", receipt, "--target", "wasm" + str(bits), "-O3", "-g", *extra]

    def vm_cmd(bits, engine):
        return [runtime, *Profile(bits).uwvm_feature_flags(), "--wasm-set-main-module-name", "main",
                "--runtime-" + engine, "--runtime-llvm-jit-cache-path", "disable",
                "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                "--ros-scene-interface", "robot", "abi", "allow"]

    header = work / "headers"
    header.mkdir()
    (header / "project.h").write_text("int calculate(int);\nint cleanup_count(void);\n")
    library = work / "library.cpp"
    library.write_text('#include "project.h"\nstatic int cleaned;\n'
                       'struct cleanup { ~cleanup() { ++cleaned; } };\n'
                       'int cleanup_count(void) { return cleaned; }\n'
                       'int calculate(int value) { if(value==42) { cleanup scope;\n'
                       'try { throw value; } catch(int caught) { if(caught!=42) __builtin_trap(); throw; }\n'
                       '} return value+7; }\n')
    caller = work / "caller.cpp"
    caller.write_text('#include <wros/scene.h>\n#include "project.h"\nextern "C" int c_value(void);\nextern "C" void _start() {\n'
                      'if (wr_abi()!=2 || calculate(5)!=EXPECTED || c_value()!=9) __builtin_trap();\n'
                      'try { calculate(42); __builtin_trap(); } catch(int v) { if(v!=42) __builtin_trap(); }\n'
                      'if(cleanup_count()!=1) __builtin_trap(); }\n')
    plain = work / "plain.c"
    plain.write_text("int c_value(void) { return 9; }\n")
    for bits in (32, 64):
        stem = "wasm" + str(bits)
        body, obj, lib, module = [work / (stem + suffix) for suffix in ("-body.o", "-lib.o", ".a", ".wasm")]
        run(stem + "-compile-library", compile_cmd(bits, "cpp", "--std", "c++20", "-I", header, "-c", library, "-o", obj))
        run(stem + "-compile-caller", compile_cmd(bits, "cpp", "-I", header, "-DEXPECTED=12", "-c", caller, "-o", body))
        c_obj = work / (stem + "-c.o")
        run(stem + "-compile-c", compile_cmd(bits, "c", "--std", "c17", "-c", plain, "-o", c_obj))
        run(stem + "-archive", [front / "bin/wrar", "--toolchain", toolchain, "-o", lib, obj, c_obj])
        archive_hash = sha(lib)
        run(stem + "-archive-reproducible", [front / "bin/wrar", "--toolchain", toolchain, "-o", lib, obj, c_obj])
        if sha(lib) != archive_hash:
            raise RuntimeError("static archive is not deterministic")
        link = compile_cmd(bits, "cpp", "--reactor", "--export", "_start", body, lib, "-o", module)
        run(stem + "-link", link)
        for engine in ("int", "aot"):
            run(stem + "-exceptions-" + engine, [*vm_cmd(bits, engine), "--run", module])
            run(stem + "-exceptions-mte-disabled-" + engine, [*vm_cmd(bits, engine), "--runtime-disable-memtag", "--run", module])
        result["artifacts"][module.name] = dict(sha256=sha(module), imports=inspect(module.read_bytes()),
            object_note=check_object(read_bounded(body)))
        old = sha(module)
        invalid = work / (stem + "-damaged.o")
        invalid.write_bytes(body.read_bytes().replace(b"producers", b"producesX", 1))
        run(stem + "-tamper", compile_cmd(bits, "cpp", "--reactor", "--export", "_start", invalid, lib, "-o", module), False, "digest mismatch")
        if sha(module) != old:
            raise RuntimeError("rejected object replaced existing output")

    # A real SDK-built object with another EH closure must not silently mix.
    noeh = work / "noeh.o"
    run("noeh-object", compile_cmd(32, "c", "--no-eh", "-c", plain, "-o", noeh))
    for label, objects in (("width", [work / "wasm32-lib.o", work / "wasm64-lib.o"]),
                           ("eh", [work / "wasm32-lib.o", noeh])):
        run("archive-refuse-" + label, [front / "bin/wrar", "--toolchain", toolchain, "-o", work / "mixed.a", *objects], False, "profile mismatch")
        run("link-refuse-" + label, compile_cmd(32, "cpp", "--reactor", "--export", "_start", work / "wasm32-body.o", objects[-1], "-o", work / "mixed.wasm"), False, "profile mismatch")
        if (work / "mixed.a").exists() or (work / "mixed.wasm").exists():
            raise RuntimeError("mismatching profile produced an output")

    # Unused archives are inspected too; a foreign byte stream cannot be hidden
    # behind a symbol index or accepted only because no symbol was referenced.
    bad_archive = work / "native.a"
    bad_archive.write_bytes(b"!<thin>\n")
    run("thin-archive-refused", compile_cmd(32, "cpp", "--reactor", "--export", "_start", work / "wasm32-body.o", bad_archive, "-o", work / "bad.wasm"), False, "ordinary GNU archive")

    # A matching build note must never authorize a dangerous final host import.
    denied_source, denied_object, denied_library = [work / name for name in ("socket.c", "socket.o", "socket.a")]
    denied_source.write_text('__attribute__((import_module("wasi_snapshot_preview1"),import_name("sock_send")))\n'
                             'extern unsigned send_raw(unsigned,unsigned,unsigned,unsigned);\n'
                             'void _start(void) { if(send_raw(1,2,3,4)) __builtin_trap(); }\n')
    run("socket-object", compile_cmd(32, "c", "-c", denied_source, "-o", denied_object))
    run("socket-archive", [front / "bin/wrar", "--toolchain", toolchain, "-o", denied_library, denied_object])
    preserved = work / "wasm32.wasm"
    before = sha(preserved)
    run("socket-final-import-refused", compile_cmd(32, "c", "--reactor", "--export", "_start", denied_library, "-o", preserved), False, "unauthorized import or signature")
    if sha(preserved) != before:
        raise RuntimeError("forbidden archive import replaced existing output")

    # Assertions retain their observable failure without acquiring stderr/files.
    assertion = work / "assertion.c"
    assertion.write_text('#include <assert.h>\nvoid _start(void) { volatile int value=0; assert(value); }\n')
    for bits in (32, 64):
        module = work / f"assertion{bits}.wasm"
        run(f"assertion{bits}-compile", compile_cmd(bits, "c", "--reactor", "--export", "_start", assertion, "-o", module))
        if inspect(module.read_bytes()):
            raise RuntimeError("pure assertion unexpectedly imports a host API")
        for engine in ("int", "aot"):
            run(f"assertion{bits}-{engine}", [*vm_cmd(bits, engine), "--run", module], False, "[crash] unreachable")

    # Both real WASI sysroot adapters and both runtime engines are exercised.
    env_source = work / "environment.c"
    env_source.write_text('#include <wasi/api.h>\n#include <stdint.h>\n'
        'void _start(void) { __wasi_size_t count=99, size=99;\n'
        'int error=__wasi_environ_sizes_get(&count, &size);\n'
        '#if EXPECT_DENIED\nif(error!=__WASI_ERRNO_NOTCAPABLE || count!=99 || size!=99) __builtin_trap();\n'
        '#else\nif(error || count!=1 || size!=10) __builtin_trap();\n'
        'uint8_t *items[2]={0}; uint8_t buffer[32]={0};\n'
        'if(__wasi_environ_get(items,buffer) || items[0]!=buffer || buffer[0]!=\'W\' || buffer[8]!=\'1\' || buffer[9]) __builtin_trap();\n'
        '#endif\n}\n')
    for bits in (32, 64):
        suffix = "_wasm64" if bits == 64 else ""
        for denied in (False, True):
            label = f"environment{bits}-" + ("denied" if denied else "allowed")
            module = work / (label + ".wasm")
            run(label + "-compile", compile_cmd(bits, "c", "--reactor", "--export", "_start", "-DEXPECT_DENIED=" + str(int(denied)), env_source, "-o", module))
            imports = inspect(module.read_bytes())
            if not any(row["name"] == "environ_sizes_get" + suffix for row in imports):
                raise RuntimeError("selected sysroot did not emit expected environment ABI")
            for engine in ("int", "aot"):
                args = [*vm_cmd(bits, engine), "--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                        "--wasip1-single-add-or-replace-environment", "main", "WROS_OK", "1"]
                for name in ("environ_sizes_get", "environ_get"):
                    args += ["--wasip1-single-interface", "main", name + suffix, "allow"]
                if not denied: args += ["--wasip1-single-grant", "main", "environ"]
                run(label + "-" + engine, [*args, "--run", module])
            result["artifacts"][module.name] = dict(sha256=sha(module), imports=imports)

    if any(sha(Path(p)) != value for p, value in hashes.items()):
        raise RuntimeError("qualification inputs changed while testing")
    result["complete"] = True
    result["cgroup"]["events_after"] = (Path(controller["path"]) / "memory.events").read_text()
    save()
    print("Completed", len(result["cases"]), "real compiler/archive/VM cases", flush=True)


if __name__ == "__main__":
    main()
