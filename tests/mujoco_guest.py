"""Build the controller from SDK source and compare an external TLS MuJoCo receiver with native stepping."""
import argparse
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("vm-source", "runtime", "openssl-root", "mujoco", "output", "toolchain", "sysroots32", "sysroots64"):
        p.add_argument("--" + field, required=True, type=Path)
    p.add_argument("--language", choices=("c", "cpp", "nim", "objectc", "lua"), default="c")
    p.add_argument("--candidate-mte", action="store_true", help="exercise an unqualified tagged compiler explicitly")
    p.add_argument("--producer", type=Path, help="Nim Wasm source producer")
    p.add_argument("--toolchain64", type=Path, help="base compiler prefix for a distinct wasm64 sysroot")
    p.add_argument("--objc-clang", type=Path)
    p.add_argument("--objc-runtime32", type=Path)
    p.add_argument("--objc-runtime64", type=Path)
    a = p.parse_args()
    if a.language == "objectc" and not all((a.objc_clang, a.objc_runtime32, a.objc_runtime64)):
        p.error("supply the Objective-C frontend and both runtime directories")
    if (a.producer is not None) != (a.language == "nim"):
        p.error("--producer is required for Nim")
    sys.path.insert(0, str(a.vm_source.resolve() / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite
    source = ROOT / "tests/mujoco" / ("controller." + (a.language if a.language in ("nim","lua") else "c"))
    compiler = ROOT / "bin" / {"c": "wrc", "cpp": "wrcc", "nim": "wrnim", "objectc": "wrobjc", "lua": "wrlua"}[a.language]
    sysroots = {32: a.sysroots32.resolve(), 64: a.sysroots64.resolve()}

    toolchains = {32: a.toolchain.resolve(), 64: (a.toolchain64 or a.toolchain).resolve()}
    objc_inputs = ([a.objc_clang.resolve(), *[lib.resolve()/name for lib in (a.objc_runtime32,a.objc_runtime64)
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
        app = directory / ("controller.m" if a.language == "objectc" else "controller." + a.language)
        app.write_bytes(source.read_bytes())
        options = ["-O3", "-g", "--reactor", "--export", "_start"]
        if a.language == "nim":
            options = ["-O3", "-g", "--producer", a.producer.resolve()]
            (directory / "simulation.nim").write_text(
                f"const steps* = {count}\nconst targetOffset* = {24+len(prefix)+8}\n"
                f"const success* = {str(mode=='success').lower()}\nconst crash* = {str(mode=='crash').lower()}\n"
                + "var request* = [" + ",".join(str(b) + "'u8" for b in request) + "]\n")
        if a.language == "objectc":
            lib = a.objc_runtime32 if width == 32 else a.objc_runtime64
            options += ["--objc-clang", a.objc_clang.resolve(), "--objc-runtime", lib.resolve()]
        if a.language == "lua":
            operations = ("capability.open", "driver.connect", "driver.submit", "driver.result",
                          "driver.describe", "driver.disconnect")
            options = ["--guest-seed", "1", *[arg for op in operations for arg in ("--ros-operation", op)]]
            literal = "".join(f"\\{b:03}" for b in request)
            app.write_text(f'local template = "{literal}"\nlocal steps = {count}\n'
                           f'local mode = "{mode}"\nlocal target_offset = {24+len(prefix)+8}\n' + source.read_text())
        header = directory / "simulation.h"
        header.write_text(f"#define STEPS {count}\n#define TARGET_OFFSET {24+len(prefix)+8}\n"
                          f"#define SUCCESS {int(mode=='success')}\n#define CRASH {int(mode=='crash')}\n"
                          + "static unsigned char request[] = {" + ",".join(map(str, request)) + "};\n")
        run(wasm.stem + "-compile", [sys.executable, compiler, "--target", f"wasm{width}", "--toolchain", toolchains[width],
                                    "--sysroots", sysroots[width], *(["--legacy-mte"] if a.candidate_mte else []),
                                    *options, app, "-o", wasm])
        controls = Profile(width).uwvm_feature_flags()
        if a.language == "objectc":
            controls += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                         "--wasip1-single-interface", "main", "clock_time_get_wasm64" if width == 64 else "clock_time_get", "allow",
                         "--wasip1-single-grant", "main", "realtime-clock"]
        return controls

    args = []
    for key, value in (("source-root", a.vm_source), ("runtime", a.runtime), ("openssl-root", a.openssl_root),
                       ("mujoco", a.mujoco), ("output", a.output)):
        args += ["--" + key, str(value.resolve())]
    suite.main(args, compile_guest=compile_guest, guest_name=a.language,
               guest_inputs=(source, Path(__file__), compiler, *([a.producer] if a.producer else []), *sysroots.values(), *objc_inputs,
                             *([ROOT / "language/lua/scene.hpp", ROOT / "language/lua/entry.cpp", ROOT / "third-parties/lua/lua-5.4.9.tar.gz"] if a.language == "lua" else []),
                             *[tc/"bin"/tool for tc in set(toolchains.values()) for tool in ("clang","wasm-ld")], ROOT / "include/wros/scene.h"))


if __name__ == "__main__":
    main()
