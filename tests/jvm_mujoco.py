"""Build Java or Kotlin source and compare the secured humanoid driver with native MuJoCo."""
import argparse
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("vm-source", "runtime", "openssl-root", "mujoco", "output", "toolchain", "sysroots", "bundle"):
        parser.add_argument("--" + field, required=True, type=Path)
    parser.add_argument("--language", required=True, choices=("java", "kotlin"))
    args = parser.parse_args()
    sys.path.insert(0, str(args.vm_source.resolve() / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite

    java = args.language == "java"
    ext = "java" if java else "kt"
    controller = ROOT / "tests/mujoco/jvm" / ("Controller." + ext)
    compiler = ROOT / "bin" / ("wr" + args.language)

    def compile_guest(wasm, width, deadline, mode, count, run):
        prefix = b"".join(suite.u64(1) for _ in range(6))
        prefix += suite.profile("simulation.position") + suite.profile("simulation.radian.logical")
        prefix += suite.text("simulation.joint") + suite.text("le64")
        canonical = prefix + suite.blob(struct.pack("<d", 2.0 if mode == "range" else 0.5))
        canonical += suite.u64(0)*2 + suite.u64(deadline)
        data = ",".join(str(n if n < 128 else n-256) for n in canonical)
        success, crash = str(mode == "success").lower(), str(mode == "crash").lower()
        directory = wasm.parent / (wasm.stem + "-source")
        directory.mkdir()
        settings = directory / ("Settings." + ext)
        if java:
            contents = (f"package simulation; final class Settings {{static final long DEADLINE={deadline}L; "
                        f"static final int TARGET={len(prefix)+8}, STEPS={count}; "
                        f"static final boolean SUCCESS={success}, CRASH={crash}; "
                        f"static byte[] payload(){{return new byte[]{{{data}}};}} }}")
        else:
            contents = (f"package simulation\nconst val DEADLINE={deadline}L\nconst val TARGET={len(prefix)+8}\n"
                        f"const val STEPS={count}\nconst val SUCCESS={success}\nconst val CRASH={crash}\n"
                        f"fun payload()=byteArrayOf({data})\n")
        settings.write_text(contents)
        run(wasm.stem+"-compile", [sys.executable, compiler, "--toolchain", args.toolchain.resolve(), "--sysroots",
                                   args.sysroots.resolve(), "--bundle", args.bundle.resolve(), "--legacy-mte",
                                   "--main-class", "simulation.Controller", controller, settings, "-o", wasm])
        imports = {(x["module"],x["name"]) for x in inspect(wasm.read_bytes())}
        allowed = {"capability.open","driver.connect","driver.submit","driver.result","driver.disconnect"}
        if mode == "crash": allowed.add("driver.describe")
        assert imports == {("uwvm_ros_v2",name) for name in allowed}, imports
        return Profile().uwvm_feature_flags()

    argv=[]
    for key,value in (("source-root",args.vm_source),("runtime",args.runtime),("openssl-root",args.openssl_root),
                      ("mujoco",args.mujoco),("output",args.output)):
        argv.extend(["--"+key,str(value.resolve())])
    sources = ROOT / "language/jvm"
    suite.main(argv, compile_guest=compile_guest,guest_name=args.language,guest_widths=(32,),
               guest_inputs=(controller, Path(__file__), compiler, args.sysroots.resolve(), sources/"Admit.java",
                             sources/"jvm_frontend.py", sources/"contracts.h", sources/"java/wros/scene/Driver.java",
                             ROOT/"language"/args.language/"host-inputs.json", ROOT/"include/wros/scene.h",
                             args.toolchain.resolve()/"bin/clang", args.toolchain.resolve()/"bin/wasm-ld"))


if __name__ == "__main__":
    main()
