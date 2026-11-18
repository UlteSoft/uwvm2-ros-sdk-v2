"""Build the controller from SDK source and compare an external TLS MuJoCo receiver with native stepping."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
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
    p.add_argument("--language", choices=("c", "cpp", "nim", "objectc", "lua", "rs", "tinygo", "fortran", "csharp"), default="c")
    p.add_argument("--candidate-mte", action="store_true", help="exercise an unqualified tagged compiler explicitly")
    p.add_argument("--installed-sdk", type=Path, help="compile with an installed SDK; a signed Objective-C site can supply its own tools and sysroots")
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
    if (a.rustroot is not None) != (a.language == "rs"):
        p.error("--rustroot is required for Rust")
    if any((path is not None) != (a.language == "tinygo") for path in (a.goroot, a.tinygoroot)):
        p.error("--goroot and --tinygoroot are required for TinyGo")
    widths = (32,) if a.language in ("rs", "tinygo", "csharp") else (32, 64)
    site = None
    if a.language == "objectc" and a.installed_sdk:
        explicit = (a.toolchain, a.toolchain64, a.sysroots32, a.sysroots64, a.objc_clang, a.objc_runtime32, a.objc_runtime64)
        if not any(explicit):
            site = local_release.site_config(compiler_root)
    if site:
        rows = local_release.verified_releases(site["trust"])
        row = select_site_release(rows, "objectc", site.get("release_sha256"))
        with a.runtime.open("rb") as stream:
            vm_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if row["vm_sha256"] != vm_digest:
            p.error("the VM differs from the signed Objective-C site release")
        profile = Profile(**{name: row["profile"][name] for name in Profile.__dataclass_fields__})
        widths = (profile.address_bits,)
        a.toolchain = Path(site["toolchain"])
        a.objc_clang = a.toolchain / "bin/wros-objc-clang"
    if a.address_bits:
        if a.address_bits not in widths:
            p.error("the requested address width is unavailable for this language")
        widths = (a.address_bits,)
    sysroots = {width: getattr(a, "sysroots" + str(width)) for width in widths}
    if not a.toolchain or (not site and not all(sysroots.values())):
        p.error("supply the toolchain and a sysroot for each selected width, or an installed Objective-C site")
    objc_runtimes = ({profile.address_bits: a.toolchain / "share/wros/objectc" / profile.identity} if site else
                     {32: a.objc_runtime32, 64: a.objc_runtime64})
    objc_runtimes = {width: objc_runtimes[width] for width in widths}
    if a.language == "objectc" and (not a.objc_clang or not all(objc_runtimes.values())):
        p.error("supply the Objective-C frontend and the runtime for each selected width")
    if (a.producer is not None) != (a.language == "nim"):
        p.error("--producer is required for Nim")
    sys.path.insert(0, str(a.vm_source.resolve() / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite
    source = ROOT / "tests/mujoco" / ("controller." + {"csharp": "c", "cpp": "c", "objectc": "c", "tinygo": "go", "fortran": "f90"}.get(a.language, a.language))
    compiler = compiler_root / "bin" / {"c": "wrc", "csharp": "wrc", "cpp": "wrcc", "nim": "wrnim", "objectc": "wrobjc", "lua": "wrlua", "fortran": "wrf", "rs": "wrrs", "tinygo": "wrtg"}[a.language]
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
        if a.language == "nim":
            options = ["-O3", "-g", "--producer", a.producer.resolve()]
            (directory / "simulation.nim").write_text(
                f"const steps* = {count}\nconst targetOffset* = {24+len(prefix)+8}\n"
                f"const success* = {str(mode=='success').lower()}\nconst crash* = {str(mode=='crash').lower()}\n"
                + "var request* = [" + ",".join(str(b) + "'u8" for b in request) + "]\n")
        if a.language == "objectc" and not site:
            options += ["--objc-clang", a.objc_clang.resolve(), "--objc-runtime", objc_runtimes[width].resolve()]
        if a.language == "lua":
            operations = ("capability.open", "driver.connect", "driver.submit", "driver.result",
                          "driver.describe", "driver.disconnect")
            options = ["--guest-seed", "1", *[arg for op in operations for arg in ("--ros-operation", op)]]
            literal = "".join(f"\\{b:03}" for b in request)
            app.write_text(f'local template = "{literal}"\nlocal steps = {count}\n'
                           f'local mode = "{mode}"\nlocal target_offset = {24+len(prefix)+8}\n' + source.read_text())
        if a.language == "fortran":
            app.write_text(fortran_settings(request, 24+len(prefix)+8, count, mode) + source.read_text())
            options = ["--eh", "-O3", "-g", *(["--flang", a.flang.resolve()] if a.flang else [])]
        if a.language == "rs":
            options = ["--rustroot", a.rustroot.resolve(), "-O3", "-g"]
            (directory / "simulation.rs").write_text(
                f"const STEPS:u64={count};\nconst TARGET:usize={24+len(prefix)+8};\n"
                f"const SUCCESS:bool={str(mode=='success').lower()};\nconst CRASH:bool={str(mode=='crash').lower()};\n"
                f"const TEMPLATE:[u8;{len(request)}]=[" + ",".join(map(str, request)) + "];\n")
        if a.language == "tinygo":
            options = ["--goroot", a.goroot.resolve(), "--tinygoroot", a.tinygoroot.resolve()]
            (directory / "go.mod").write_text("module example.local/mujoco\n\ngo 1.24\n\nrequire wros.local/scene v0.0.0\n"
                + "replace wros.local/scene => " + json.dumps(str(ROOT / "language/tinygo/scene")) + "\n")
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
            run(wasm.stem + "-verify", [sys.executable, "-B", compiler_root / "install/qualification.py", "--artifact", wasm,
                                        "--receipt", receipt, "--vm", a.runtime.resolve(), "--approved-receipt-sha256",
                                        hashlib.sha256(receipt.read_bytes()).hexdigest()])
        controls = Profile(width, exceptions="noeh" if a.language == "rs" else "eh").uwvm_feature_flags()
        if a.language == "objectc":
            controls += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                         "--wasip1-single-interface", "main", "clock_time_get_wasm64" if width == 64 else "clock_time_get", "allow",
                         "--wasip1-single-grant", "main", "realtime-clock"]
        return controls

    args = []
    for key, value in (("source-root", a.vm_source), ("runtime", a.runtime), ("openssl-root", a.openssl_root),
                       ("mujoco", a.mujoco), ("output", a.output)):
        args += ["--" + key, str(value.resolve())]
    if a.vendor_model:
        args.extend(["--vendor-model",str(a.vendor_model.resolve()),"--vendor-assets",str(a.vendor_assets.resolve()),
                     "--platform-targets",str(ROOT/"share/targets.json"),"--audit-calls"])
    producers = [path for path in (a.flang, a.producer) if path]
    if a.language == "csharp":
        producers.extend((compiler_root / "bin/wrcs", ROOT / "tests/mujoco/controller.cs",
                          *(ROOT / "language/csharp" / file for file in ("inputs.sha256", "Admit.cs", "leaf.cpp", "numeric.py", "host.py"))))
    if a.language == "rs":
        producers.extend((a.rustroot / "bin/rustc", ROOT / "language/rust/scene.rs", ROOT / "tools/wasm/tag_ir.cpp"))
    if a.language == "tinygo":
        producers.extend((a.goroot / "bin/go", a.tinygoroot / "bin/tinygo", ROOT / "language/tinygo/scene/scene_wros.go",
                          ROOT / "tools/wasm/tag_ir.cpp"))
    suite.main(args, compile_guest=compile_guest, guest_name=a.language, guest_widths=widths,
               guest_inputs=(source, Path(__file__), compiler, *producers, *manifests, *objc_inputs,
                             *([compiler_root / "language/lua/scene.hpp", compiler_root / "language/lua/entry.cpp", compiler_root / "third-parties/lua/lua-5.4.9.tar.gz"] if a.language == "lua" else []),
                             *[tc/"bin"/tool for tc in {toolchains[w] for w in widths} for tool in ("clang","wasm-ld")], compiler_root / "include/wros/scene.h"))


if __name__ == "__main__":
    main()
