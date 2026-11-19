"""@brief Drive a vendor MuJoCo model through an isolated ROS driver using compiled standard Go."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


DRIVE = """package robot

// @brief Select the signed test setpoint from the current simulation step.
// @param step Simulation step counter.
// @return Negative one for even steps and positive one for odd steps.
func Drive(step uint32) int32 {
    if step & 1 == 0 {
        return -1
    }
    return 1
}

// @brief Report successful startup.
func Start() uint32 { return 0 }
"""


def main():
    """@brief Compare the installed Go setpoint calculation with the native physics reference.
    @details A Wasm fixture owns the explicitly granted driver capability, marshals
    its bounded requests and polls the result. The separate, register-only Go
    module supplies the signed command signal for every successful simulation step.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm-source", "runtime", "mujoco", "openssl-root", "vendor-model", "vendor-assets", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    vm_tests = args.vm_source.resolve() / "test/0084.ros-runtime"
    sys.path.insert(0, str(vm_tests))
    import run_driver_mujoco as simulation
    simulation.verify_gate()
    root = args.sdk.resolve()
    compiler = root / "bin/wrgo"
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    vendor = json.loads(args.vendor_model.read_bytes())
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp)
        source = stage / "controller.go"
        source.write_text(DRIVE)
        algorithm = stage / "algorithm.wasm"
        subprocess.run([compiler, source, "-o", algorithm, "--build-receipt"], check=True, timeout=120)
        targets = stage / "platform.json"
        targets.write_text(json.dumps({"platforms": {vendor["platform"]: ["go"]}}))

        def compile_adapter(wasm, width, deadline, mode, count, run):
            fixture = simulation.guest(width, 0, deadline, mode, count)
            probe = ("i32.const 0 call $drive i32.const -1 i32.ne if unreachable end "
                     "i32.const 1 call $drive i32.const 1 i32.ne if unreachable end")
            fixture.body.insert(0, probe)
            text = fixture.render()
            module_start = "(module\n"
            if not text.startswith(module_start):
                raise ValueError("unsupported VM test adapter module format")
            binding = '(import "algorithm" "Drive" (func $drive (param i32) (result i32)))\n'
            text = module_start + binding + text[len(module_start):]
            if mode == "success":
                native_law = ("global.get $sequence i64.const 1 i64.and i64.eqz if (result i64) "
                              "i64.const -4620693217682128896 else i64.const 4602678819172646912 end")
                if text.count(native_law) != 1:
                    raise ValueError("VM fixture did not expose exactly one native setpoint calculation")
                go_law = ("global.get $sequence i32.wrap_i64 call $drive f64.convert_i32_s "
                          "f64.const 0.5 f64.mul i64.reinterpret_f64")
                text = text.replace(native_law, go_law)
            wat = wasm.with_suffix(".wat")
            wat.write_text(text)
            run(wasm.stem + "-adapter", ["wat2wasm", "--enable-multi-memory", "--debug-names", wat, "-o", wasm])
            return ["--wasm-preload-library", str(algorithm), "algorithm", "--runtime-memtag-mode", "sync"]

        flags = ["--runtime", args.runtime, "--source-root", args.vm_source, "--mujoco", args.mujoco,
                 "--openssl-root", args.openssl_root, "--vendor-model", args.vendor_model,
                 "--vendor-assets", args.vendor_assets, "--output", output, "--platform-targets", targets]
        status = simulation.main(list(map(str, flags)), compile_guest=compile_adapter, guest_widths=(32,),
                                 guest_name="standard-Go conditional scalar law, Wasm driver test adapter",
                                 guest_inputs=(compiler, source, algorithm, Path(__file__)))
        if status:
            return status
        # Preserve the exact control module and its producer/authority evidence.
        (output / "controller.go").write_bytes(source.read_bytes())
        (output / "algorithm.wasm").write_bytes(algorithm.read_bytes())
        (output / "algorithm.wasm.wros-go.json").write_bytes(Path(str(algorithm) + ".wros-go.json").read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
