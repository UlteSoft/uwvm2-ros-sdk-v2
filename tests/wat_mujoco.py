"""@file wat_mujoco.py
@brief Test SDK-assembled WAT against a locally supplied vendor MuJoCo model.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile


def main():
    """@brief Run the existing driver fixture with the installed SDK's WAT assembler."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm-source", "runtime", "mujoco", "openssl-root", "vendor-model", "vendor-assets", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    root = args.sdk.resolve(strict=True)
    vm_source = args.vm_source.resolve(strict=True)
    sys.path.insert(0, str(vm_source / "test/0084.ros-runtime"))
    import run_driver_mujoco as simulation

    simulation.verify_gate()
    assembler = root / "bin/wrwat"
    profile = json.loads(args.vendor_model.read_bytes())
    platform = profile["platform"]
    if root.parent.name != "wat" or root.parent.parent.name != platform:
        raise ValueError("the vendor model must match the installed WAT platform")
    output = args.output.resolve()

    def compile_guest(wasm, width, deadline, mode, count, run):
        fixture = simulation.guest(width, 0, deadline, mode, count)
        source = wasm.with_suffix(".wat")
        source.write_text(fixture.render())
        command = [assembler, source, "--target", f"wasm{width}", "--no-mte", "-g", "--build-receipt", "-o", wasm]
        if fixture.open_import:
            command.extend(("--ros-operation", "capability.open"))
        for operation in fixture.operations:
            command.extend(("--ros-operation", operation["name"]))
        run(wasm.stem + "-sdk-assembly", command)
        return ["--runtime-disable-memtag"]

    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        selected = Path(directory) / "platform.json"
        selected.write_text(json.dumps({"platforms": {platform: ["wat"]}}))
        flags = [
            "--runtime", args.runtime, "--source-root", vm_source, "--mujoco", args.mujoco,
            "--openssl-root", args.openssl_root, "--vendor-model", args.vendor_model, "--vendor-assets",
            args.vendor_assets, "--platform-targets", selected, "--output", output,
        ]
        return simulation.main(list(map(str, flags)), compile_guest=compile_guest, guest_widths=(32, 64),
                               guest_name="SDK wrwat, explicit untagged linear memory",
                               guest_inputs=(assembler, root / "language/wat/driver.py", Path(__file__)))


if __name__ == "__main__":
    raise SystemExit(main())
