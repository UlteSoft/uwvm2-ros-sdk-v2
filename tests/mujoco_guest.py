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
    p.add_argument("--language", choices=("c", "cpp", "nim"), default="c")
    p.add_argument("--candidate-mte", action="store_true", help="exercise an unqualified tagged compiler explicitly")
    p.add_argument("--producer", type=Path, help="Nim Wasm source producer")
    a = p.parse_args()
    if (a.producer is not None) != (a.language == "nim"):
        p.error("--producer is required for Nim")
    sys.path.insert(0, str(a.vm_source.resolve() / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite
    source = ROOT / ("tests/mujoco/controller.nim" if a.language == "nim" else "tests/mujoco/controller.c")
    compiler = ROOT / "bin" / {"c": "wrc", "cpp": "wrcc", "nim": "wrnim"}[a.language]
    sysroots = {32: a.sysroots32.resolve(), 64: a.sysroots64.resolve()}

    def compile_guest(wasm, width, deadline, mode, count, run):
        prefix = b"".join(suite.u64(1) for _ in range(6))
        prefix += suite.profile("simulation.position") + suite.profile("simulation.radian.logical")
        prefix += suite.text("simulation.joint") + suite.text("le64")
        payload = prefix + suite.blob(struct.pack("<d", 2.0 if mode == "range" else 0.5))
        payload += suite.u64(0) * 2 + suite.u64(deadline)
        request = suite.u64(1) + suite.u64(deadline) + suite.blob(payload)
        directory = wasm.parent / (wasm.stem + "-source")
        directory.mkdir()
        app = directory / ("controller." + a.language)
        app.write_bytes(source.read_bytes())
        options = ["--reactor", "--export", "_start"]
        if a.language == "nim":
            options = ["--producer", a.producer.resolve()]
            (directory / "simulation.nim").write_text(
                f"const steps* = {count}\nconst targetOffset* = {24+len(prefix)+8}\n"
                f"const success* = {str(mode=='success').lower()}\nconst crash* = {str(mode=='crash').lower()}\n"
                + "var request* = [" + ",".join(str(b) + "'u8" for b in request) + "]\n")
        header = directory / "simulation.h"
        header.write_text(f"#define STEPS {count}\n#define TARGET_OFFSET {24+len(prefix)+8}\n"
                          f"#define SUCCESS {int(mode=='success')}\n#define CRASH {int(mode=='crash')}\n"
                          + "static unsigned char request[] = {" + ",".join(map(str, request)) + "};\n")
        run(wasm.stem + "-compile", [sys.executable, compiler, "--target", f"wasm{width}", "--toolchain", a.toolchain,
                                    "--sysroots", sysroots[width], *(["--legacy-mte"] if a.candidate_mte else []),
                                    "-O3", "-g", *options, app, "-o", wasm])
        return Profile(width).uwvm_feature_flags()

    args = []
    for key, value in (("source-root", a.vm_source), ("runtime", a.runtime), ("openssl-root", a.openssl_root),
                       ("mujoco", a.mujoco), ("output", a.output)):
        args += ["--" + key, str(value.resolve())]
    suite.main(args, compile_guest=compile_guest, guest_name=a.language,
               guest_inputs=(source, Path(__file__), compiler, *([a.producer] if a.producer else []), *sysroots.values(), a.toolchain / "bin/clang",
                             a.toolchain / "bin/wasm-ld", ROOT / "include/wros/scene.h"))


if __name__ == "__main__":
    main()
