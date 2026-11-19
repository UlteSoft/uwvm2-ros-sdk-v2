"""@file mujoco_guest.py
@brief Compare a Wasm controller using an isolated TLS MuJoCo receiver with native stepping.
@details Signed development-site runs bind the VM and compiler release before building;
each generated controller and its receipt are verified before the simulation starts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from imports import inspect
import local_release
from qualification import select_site_release


def fortran_settings(request, target_offset, count, mode):
    """Emit initialized, guest-owned bytes in portable signed ISO C integer kinds."""
    signed = [str(b if b < 128 else b - 256) for b in request]
    rows = [", ".join(signed[i:i+16]) for i in range(0, len(signed), 16)]
    return ("module simulation\n  use iso_c_binding, only: c_int8_t\n  implicit none\n"
            f"  integer, parameter :: steps={count}, target_offset={target_offset}\n"
            f"  logical, parameter :: success=.{str(mode == 'success').lower()}., crash=.{str(mode == 'crash').lower()}.\n"
            f"  integer(c_int8_t), target :: request({len(signed)})=[integer(c_int8_t) :: &\n    "
            + ", &\n    ".join(rows) + "]\nend module\n")


def main():
    """@brief Compile and verify each requested guest configuration and run the receiver scenarios."""
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("vm-source", "runtime", "openssl-root", "mujoco", "output"):
        p.add_argument("--" + field, required=True, type=Path)
    p.add_argument("--toolchain", type=Path)
    p.add_argument("--sysroots32", type=Path)
    p.add_argument("--sysroots64", type=Path, help="matching wasm64 sysroot for dual-width toolchains")
    p.add_argument("--address-bits", type=int, choices=(32, 64),
                   help="exercise one address width from the selected language toolchain")
    p.add_argument("--vendor-model", type=Path, help="a pinned platform MJCF manifest from the VM fixtures")
    p.add_argument("--vendor-assets", type=Path, help="the original model files listed in the manifest")
    p.add_argument("--language", choices=("c", "cpp", "d", "nim", "objectc", "lua", "js", "py", "rs", "tinygo", "fortran", "csharp"), default="c")
    p.add_argument("--candidate-mte", action="store_true", help="exercise an unqualified tagged compiler explicitly")
    p.add_argument("--installed-sdk", type=Path, help="compile with an installed SDK; signed D, Fortran, Nim, Objective-C, Rust and TinyGo sites supply their own tools and sysroots")
    p.add_argument("--producer", type=Path, help="Nim Wasm source producer")
    p.add_argument("--toolchain64", type=Path, help="base compiler prefix for a distinct wasm64 sysroot")
    p.add_argument("--objc-clang", type=Path)
    p.add_argument("--objc-runtime32", type=Path)
    p.add_argument("--objc-runtime64", type=Path)
    p.add_argument("--flang", type=Path, help="Fortran compiler from the selected toolchain")
    p.add_argument("--rustroot", type=Path, help="pinned Rust compiler installation")
    p.add_argument("--goroot", type=Path, help="pinned Go installation for TinyGo")
    p.add_argument("--tinygoroot", type=Path, help="pinned TinyGo installation")
    p.add_argument("--dotnet", type=Path, help="pinned host .NET SDK for the C# numeric component")
    p.add_argument("--mono-compiler", type=Path, help="pinned host Mono LLVMOnly compiler")
    a = p.parse_args()
    if bool(a.vendor_model) != bool(a.vendor_assets):
        p.error("supply both the vendor model and its asset directory")
    if a.vendor_model and a.installed_sdk:
        platform = json.loads(a.vendor_model.read_bytes())["platform"]
        if a.installed_sdk.resolve(strict=True).parents[1].name != platform:
            p.error("the model platform differs from the installed SDK selection")
    if a.installed_sdk and a.candidate_mte:
        p.error("the installed SDK simulation requires a qualified compiler")
    compiler_root = a.installed_sdk.resolve(strict=True) if a.installed_sdk else ROOT
    if any((path is not None) != (a.language == "csharp") for path in (a.dotnet, a.mono_compiler)):
        p.error("--dotnet and --mono-compiler are required together for C#")
    if a.flang and a.language != "fortran":
        p.error("--flang applies to Fortran")
    widths = (32,) if a.language in ("rs", "tinygo", "csharp", "js", "d") else (32, 64)
    site = None
    explicit = (a.toolchain, a.toolchain64, a.sysroots32, a.sysroots64, a.objc_clang, a.objc_runtime32, a.objc_runtime64, a.goroot, a.tinygoroot, a.producer, a.rustroot, a.flang)
    if a.language in ("d", "objectc", "tinygo", "nim", "rs", "fortran", "py") and a.installed_sdk and not any(explicit):
        site = local_release.site_config(compiler_root)
    if a.language == "py" and not site:
        p.error("Python requires a signed installed C site and the matching CPython target")
    if not site and (a.rustroot is not None) != (a.language == "rs"):
        p.error("provide --rustroot for an explicit Rust toolchain")
    if not site and any((path is not None) != (a.language == "tinygo") for path in (a.goroot, a.tinygoroot)):
        p.error("provide explicit Go and TinyGo roots or use an installed signed TinyGo site")
    if a.language == "d" and (not site or not (compiler_root / "bin/wrd").is_file()):
        p.error("D BetterC requires --installed-sdk pointing to a signed D site without toolchain overrides")
    if site:
        if a.language == "d":
            sys.path.insert(0, str(compiler_root / "language/d"))
            from release import authorized
            row = authorized(site)
        else:
            rows = local_release.verified_releases(site["trust"])
            backend = "c" if a.language == "py" else a.language
            row = select_site_release(rows, backend, site.get("release_sha256"))
        with a.runtime.open("rb") as stream:
            vm_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if row["vm_sha256"] != vm_digest:
            p.error("the VM differs from the signed " + a.language + " site release")
        profile = Profile(**{name: row["profile"][name] for name in Profile.__dataclass_fields__})
        widths = (profile.address_bits,)
        a.toolchain = Path(site["toolchain"])
        if a.language == "tinygo":
            a.goroot = a.toolchain / "libexec/wros/go"
            a.tinygoroot = a.toolchain / "libexec/wros/tinygo"
        if a.language == "rs":
            a.rustroot = a.toolchain / "libexec/wros/rust"
        if a.language == "nim":
            a.producer = a.toolchain / "bin/wrnim-lower"
        if a.language == "fortran":
            a.flang = a.toolchain / "bin/flang"
        if a.language == "objectc":
            a.objc_clang = a.toolchain / "bin/wros-objc-clang"
    if a.address_bits:
        if a.address_bits not in widths:
            p.error("the requested address width is unavailable for this language")
        widths = (a.address_bits,)
    sysroots = {width: getattr(a, "sysroots" + str(width)) for width in widths}
    if not a.toolchain or (not site and not all(sysroots.values())):
        p.error("supply the toolchain and a sysroot for each selected width, or an installed signed language site")
    objc_runtimes = ({profile.address_bits: a.toolchain / "share/wros/objectc" / profile.identity} if site and a.language == "objectc" else
                     {32: a.objc_runtime32, 64: a.objc_runtime64})
    objc_runtimes = {width: objc_runtimes[width] for width in widths}
    if a.language == "objectc" and (not a.objc_clang or not all(objc_runtimes.values())):
        p.error("supply the Objective-C frontend and the runtime for each selected width")
    if (a.producer is not None) != (a.language == "nim"):
        p.error("--producer is required for Nim")
    sys.path.insert(0, str(a.vm_source.resolve() / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite
    source = ROOT / "tests/mujoco" / ("controller." + {"csharp": "c", "cpp": "c", "objectc": "c", "tinygo": "go", "fortran": "f90"}.get(a.language, a.language))
    compiler = compiler_root / "bin" / {"d": "wrd", "c": "wrc", "csharp": "wrc", "cpp": "wrcc", "nim": "wrnim", "objectc": "wrobjc", "lua": "wrlua", "js": "wrjs", "py": "wrpy", "fortran": "wrf", "rs": "wrrs", "tinygo": "wrtg"}[a.language]
    manifests = list(map(Path, site["sysroots"])) if site else [path.resolve() for path in sysroots.values()]

    toolchains = {32: a.toolchain.resolve(), 64: (a.toolchain64 or a.toolchain).resolve()}
    objc_inputs = ([a.objc_clang.resolve(), *[lib.resolve()/name for lib in objc_runtimes.values()
                    for name in ("runtime.json", "libobjc.a")]] if a.language == "objectc" else [])

    def compile_guest(wasm, width, deadline, mode, count, run):
        prefix = b"".join(suite.u64(1) for _ in range(6))
        prefix += suite.profile("simulation.position") + suite.profile("simulation.radian.logical")
        prefix += suite.text("simulation.joint") + suite.text("le64")
        payload = prefix + suite.blob(struct.pack("<d", 2.0 if mode == "range" else 0.5))
        payload += suite.u64(0) * 2 + suite.u64(deadline)
        request = suite.u64(1) + suite.u64(deadline) + suite.blob(payload)
        directory = wasm.parent / (wasm.stem + "-source")
        directory.mkdir()
        app = directory / ("controller." + {"objectc": "m", "fortran": "f90", "tinygo": "go", "csharp": "c"}.get(a.language, a.language))
        app.write_bytes(source.read_bytes())
        options = ["-O3", "-g", "--reactor", "--export", "_start"]
        if a.language == "d":
            options = ["-O3", "-g"]
            prelude = (f"module application;\nenum steps = {count}; enum targetOffset = {24+len(prefix)+8};\n"
                       f"enum bool success = {str(mode=='success').lower()}; enum bool crash = {str(mode=='crash').lower()};\n"
                       f"__gshared ubyte[{len(request)}] request = [" + ",".join(map(str, request)) + "];\n")
            app.write_text(prelude + source.read_text())
        if a.language == "nim":
            options = [] if site else ["-O3", "-g", "--producer", a.producer.resolve()]
            (directory / "simulation.nim").write_text(
                f"const steps* = {count}\nconst targetOffset* = {24+len(prefix)+8}\n"
                f"const success* = {str(mode=='success').lower()}\nconst crash* = {str(mode=='crash').lower()}\n"
                + "var request* = [" + ",".join(str(b) + "'u8" for b in request) + "]\n")
        if a.language == "objectc" and not site:
            options += ["--objc-clang", a.objc_clang.resolve(), "--objc-runtime", objc_runtimes[width].resolve()]
        if a.language in ("js", "py"):
            operations = ("capability.open", "clock.create", "clock.read", "driver.connect", "driver.submit", "driver.result",
                          "driver.describe", "driver.disconnect")
            options = [arg for op in operations for arg in ("--ros-operation", op)]
        if a.language == "js":
            app.write_text("const template = " + json.dumps(list(request)) + ";\n" +
                           f"const steps = {count}, targetOffset = {24+len(prefix)+8};\n" +
                           f"const mode = {json.dumps(mode)};\n" + source.read_text())
        if a.language == "py":
            app.write_text(f"template = {request!r}\nsteps = {count}\n"
                           f"target_offset = {24+len(prefix)+8}\nmode = {mode!r}\n" + source.read_text())
        if a.language == "lua":
            operations = ("capability.open", "driver.connect", "driver.submit", "driver.result",
                          "driver.describe", "driver.disconnect")
            options = ["--guest-seed", "1", *[arg for op in operations for arg in ("--ros-operation", op)]]
            literal = "".join(f"\\{b:03}" for b in request)
            app.write_text(f'local template = "{literal}"\nlocal steps = {count}\n'
                           f'local mode = "{mode}"\nlocal target_offset = {24+len(prefix)+8}\n' + source.read_text())
        if a.language == "fortran":
            app.write_text(fortran_settings(request, 24+len(prefix)+8, count, mode) + source.read_text())
            options = [] if site else ["--eh", "-O3", "-g", *(["--flang", a.flang.resolve()] if a.flang else [])]
        if a.language == "rs":
            options = [] if site else ["--rustroot", a.rustroot.resolve(), "-O3", "-g"]
            (directory / "simulation.rs").write_text(
                f"const STEPS:u64={count};\nconst TARGET:usize={24+len(prefix)+8};\n"
                f"const SUCCESS:bool={str(mode=='success').lower()};\nconst CRASH:bool={str(mode=='crash').lower()};\n"
                f"const TEMPLATE:[u8;{len(request)}]=[" + ",".join(map(str, request)) + "];\n")
        if a.language == "tinygo":
            options = [] if site else ["--goroot", a.goroot.resolve(), "--tinygoroot", a.tinygoroot.resolve()]
            (directory / "go.mod").write_text("module example.local/mujoco\n\ngo 1.24\n\nrequire wros.local/scene v0.0.0\n"
                + "replace wros.local/scene => " + json.dumps(str(compiler_root / "language/tinygo/scene")) + "\n")
            (directory / "settings.go").write_text(f"package main\nconst steps={count}\nconst targetOffset={24+len(prefix)+8}\n"
                f"const success={str(mode=='success').lower()}\nconst crash={str(mode=='crash').lower()}\n"
                + "var template=[...]byte{" + ",".join(map(str, request)) + "}\n")
            app = directory
        header = directory / "simulation.h"
        header.write_text(f"#define STEPS {count}\n#define TARGET_OFFSET {24+len(prefix)+8}\n"
                          f"#define SUCCESS {int(mode=='success')}\n#define CRASH {int(mode=='crash')}\n"
                          + "static unsigned char request[] = {" + ",".join(map(str, request)) + "};\n")
        objects = []
        if a.language == "csharp":
            obj = wasm.parent / "direction.o"
            if not obj.exists():
                run("csharp-numeric-aot", [sys.executable, compiler_root / "bin/wrcs", "--dotnet", a.dotnet.resolve(),
                    "--mono-compiler", a.mono_compiler.resolve(), "--toolchain", toolchains[width],
                    "--sysroots", sysroots[width], *(["--legacy-mte"] if a.candidate_mte else []),
                    "--entry", "SimulatedJoint.Direction", "-c", ROOT / "tests/mujoco/controller.cs", "-o", obj])
            options += ["-D", "WROS_CSHARP_CONTROL"]
            objects.append(obj)
        tool_args = ["--build-receipt"] if site else ["--toolchain", toolchains[width], "--sysroots", sysroots[width].resolve()]
        run(wasm.stem + "-compile", [sys.executable, compiler, "--target", f"wasm{width}", *tool_args, *(["--legacy-mte"] if a.candidate_mte else []),
                                    *options, app, *objects, "-o", wasm])
        if site:
            receipt = Path(str(wasm) + ".wros-build.json")
            verifier = [compiler_root / "install/qualification.py"]
            if a.language == "d":
                verifier = [compiler, "verify"]
                record = json.loads(receipt.read_bytes())
                if record.get("source_sha256") != hashlib.sha256(app.read_bytes()).hexdigest():
                    raise ValueError("the BetterC receipt refers to a different controller source")
                entries = inspect(wasm.read_bytes())
                expected = {"capability.open", "driver.connect", "driver.submit", "driver.result", "driver.disconnect"}
                if mode == "crash":
                    expected.add("driver.describe")
                if sorted((i["module"], i["name"]) for i in entries) != sorted(("uwvm_ros_v2", name) for name in expected):
                    raise ValueError("unexpected BetterC controller imports")
            run(wasm.stem + "-verify", [sys.executable, "-B", *verifier, "--artifact", wasm,
                                        "--receipt", receipt, "--vm", a.runtime.resolve(), "--approved-receipt-sha256",
                                        hashlib.sha256(receipt.read_bytes()).hexdigest()])
        guest_profile = profile if site else Profile(width, exceptions="noeh" if a.language == "rs" else "eh")
        controls = guest_profile.uwvm_feature_flags()
        if a.language in ("js", "objectc", "py"):
            suffix = "_wasm64" if width == 64 else ""
            controls += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                         "--wasip1-single-interface", "main", "clock_time_get" + suffix, "allow",
                         "--wasip1-single-grant", "main", "realtime-clock"]
            if a.language == "py":
                controls += ["--wasip1-single-interface", "main", "clock_res_get" + suffix, "allow"]
                for name in ("monotonic-clock", "realtime-resolution", "monotonic-resolution"):
                    controls += ["--wasip1-single-grant", "main", name]
        return controls

    args = []
    for key, value in (("source-root", a.vm_source), ("runtime", a.runtime), ("openssl-root", a.openssl_root),
                       ("mujoco", a.mujoco), ("output", a.output)):
        args += ["--" + key, str(value.resolve())]
    if a.vendor_model:
        args.extend(["--vendor-model",str(a.vendor_model.resolve()),"--vendor-assets",str(a.vendor_assets.resolve()),
                     "--platform-targets",str(ROOT/"share/targets.json"),"--audit-calls"])
    producers = [path for path in (a.flang, a.producer) if path]
    if site:
        producers.extend((compiler_root / "share/qualification/site-profile.json", Path(site["trust"]["statement"])))
    if a.language == "d":
        producers.extend((compiler_root / "language/d/wros_scene.d", compiler_root / "language/d/imports.c"))
    if a.language == "csharp":
        producers.extend((compiler_root / "bin/wrcs", ROOT / "tests/mujoco/controller.cs",
                          *(ROOT / "language/csharp" / file for file in ("inputs.sha256", "Admit.cs", "SceneEntry.cs", "Scene.cs", "leaf.cpp", "numeric.py", "host.py", "scalar.py"))))
    if a.language == "rs":
        producers.extend((a.rustroot / "bin/rustc", compiler_root / "language/rust/scene.rs", compiler_root / "tools/wasm/tag_ir.cpp"))
    if a.language == "tinygo":
        producers.extend((a.goroot / "bin/go", a.tinygoroot / "bin/tinygo", compiler_root / "language/tinygo/scene/scene_wros.go",
                          compiler_root / "tools/wasm/tag_ir.cpp"))
    if a.language == "js":
        producers.extend((compiler_root / "language/js/entry.c", compiler_root / "third-parties/quickjs/quickjs.c"))
    if a.language == "py":
        producers.extend(sorted((compiler_root / "language/py").glob("*.py")))
        producers.extend(sorted((compiler_root / "third-parties/cpython").glob("*")))
        producers.extend(sorted((compiler_root / "third-parties/cpython-runtime").glob("*")))
    suite.main(args, guest_steady_deadlines=a.language in ("js", "py"),
               compile_guest=compile_guest, guest_name=a.language, guest_widths=widths,
               guest_inputs=(source, Path(__file__), compiler, *producers, *manifests, *objc_inputs,
                             *([compiler_root / "language/lua/scene.hpp", compiler_root / "language/lua/entry.cpp", compiler_root / "third-parties/lua/lua-5.4.9.tar.gz"] if a.language == "lua" else []),
                             *[tc/"bin"/tool for tc in {toolchains[w] for w in widths} for tool in ("clang","wasm-ld")],
                             *([] if a.language == "rs" else [compiler_root / "include/wros/scene.h"])))


if __name__ == "__main__":
    main()
