"""@file assemblyscript_mujoco.py
@brief Run the installed AssemblyScript scalar controller with a Wasm driver fixture.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile

from separate_compilation import cgroup_record, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from artifacts import sections
from bootstrap import MAX_METADATA, Source
from imports import inspect

CONTROLLER = "assemblyscript-controller"
SCENARIOS = {"success": 0, "range": 1, "crash": 2}


def render_guest(suite, deadline, mode, count):
    """@brief Marshal the controller's scalar result into the bounded driver request."""
    g = suite.Fixture(suite.NAMES, 32, 0)
    cap = g.open("joint")
    g.extra_imports.append(f'(import "{CONTROLLER}" "jointTarget" '
                           '(func $jointTarget (param i64 i32) (result f64)))')
    g.globals.add("sequence")
    prefix = suite.u64(1) * 6 + suite.profile("simulation.position") + suite.profile("simulation.radian.logical")
    prefix += suite.text("simulation.joint") + suite.text("le64")
    payload = prefix + suite.blob(bytes(8)) + suite.u64(0) * 2 + suite.u64(deadline)
    data = suite.u64(1) + suite.u64(deadline) + suite.blob(payload)
    request = g.blob(data)
    sequence = g.blob(suite.u64(1))

    def poll(operation, address=0, size=0):
        g.extra_functions.append(f"""(func ${operation}.poll (result i32)
            (local $status i32) (local $attempt i32)
            block $done loop $retry
                {cap} i32.const 0 i64.const {address} i64.const {size}
                i64.const 16384 i64.const 512 i64.const 1024 call ${operation}
                local.tee $status i32.const 11 i32.ne br_if $done
                local.get $attempt i32.const 1 i32.add local.tee $attempt
                i32.const 10000000 i32.ge_u if unreachable end
                br $retry
            end end local.get $status)""")
        return f"call ${operation}.poll"

    g.check(poll("driver.connect"))
    g.body += ["i64.const 1 global.set $sequence", "loop $cycle"]
    for address in (request, request + 32, sequence):
        g.write(address, "global.get $sequence")
    g.write(request + 24 + len(prefix) + 8,
            f"global.get $sequence i32.const {SCENARIOS[mode]} call $jointTarget i64.reinterpret_f64")
    g.check(poll("driver.submit", request, len(data)))
    result = poll("driver.result", sequence, 8)
    if mode == "crash":
        g.extra_functions.append("""(func $loss (param $status i32)
            local.get $status i32.const 5 i32.eq local.get $status i32.const 13 i32.eq
            i32.or i32.eqz if unreachable end)""")
        g.body.append(result + " call $loss")
        g.request("driver.describe", b"", cap=cap, capacity=32)
        g.equal(g.word(16384), 6)
        g.equal(g.word(16408), 1)
    else:
        g.check(result)
        g.equal(g.word(16384), 13 if mode == "range" else 0)
        g.check(g.word(16400) + " global.get $sequence i64.ne")
    g.body += ["global.get $sequence i64.const 1 i64.add global.set $sequence",
               f"global.get $sequence i64.const {count} i64.le_u br_if $cycle", "end"]
    g.request("driver.disconnect", b"", cap=cap, capacity=8)
    return g.render()


def main():
    """@brief Install one exact SDK selection and qualify the mixed-language simulation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("vm-source", "runtime", "mujoco", "openssl-root", "vendor-model", "vendor-assets", "output"):
        parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
    args = parser.parse_args()
    if not __debug__:
        parser.error("simulation qualification requires Python assertions")
    cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    platform = json.loads(args.vendor_model.read_bytes())["platform"]
    args.output.mkdir(mode=0o700)
    sys.path.insert(0, str(args.vm_source / "test/0084.ros-runtime"))
    import run_driver_mujoco as suite

    with tempfile.TemporaryDirectory(dir=args.output, prefix="sdk-") as directory:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "XMAKE_"))}
        env.update(TMPDIR=directory, PYTHONDONTWRITEBYTECODE="1")
        with (args.output / "install.json").open("xb") as install_record:
            subprocess.run([sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
                            "--local-repository", ROOT, "--commit", args.commit, "--platform", platform,
                            "--language", "as", "--prefix", directory, "--", "--component", "development"],
                           env=env, stdout=install_record, check=True, timeout=180)
        installed = json.loads((args.output / "install.json").read_bytes())
        sdk = Path(installed["directory"])
        registry = args.output / "targets.json"
        registry.write_bytes(Source(installed["commit"], ROOT).read("share/targets.json", MAX_METADATA))
        source = ROOT / "tests/mujoco/controller.ts"
        artifact = args.output / "controller.wasm"
        with (args.output / "controller-build.log").open("xb") as log:
            subprocess.run([sdk / "bin/wras", source, "--build-receipt", "-g", "-o", artifact], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        sidecar = artifact.with_suffix(".wasm.wros-as.json")
        receipt = json.loads(sidecar.read_bytes())
        data = artifact.read_bytes()
        assert receipt["mte_requested"] is True and receipt["linear_memories"] == 0
        assert receipt["source_sha256"] == sha(source) and receipt["wasm_sha256"] == sha(artifact)
        assert inspect(data) == [] and all(data[start] not in (5, 11, 12) for start, _, _, _ in sections(data))

        def compile_guest(wasm, width, deadline, mode, count, run):
            assert width == 32
            wat = wasm.with_suffix(".wat")
            wat.write_text(render_guest(suite, deadline, mode, count))
            run(wasm.stem + "-assemble", ["wat2wasm", "--enable-multi-memory", "--debug-names", wat, "-o", wasm],
                env=env)
            imports = inspect(wasm.read_bytes())
            expected = {"module": CONTROLLER, "name": "jointTarget", "kind": 0,
                        "params": ["i64", "i32"], "results": ["f64"]}
            assert [entry for entry in imports if entry["module"] != "uwvm_ros_v2"] == [expected]
            return ["--wasip1-single-create", "main", "--wasip1-single-disable", "main",
                    "--wasip1-single-create", CONTROLLER, "--wasip1-single-disable", CONTROLLER,
                    "--wasm-preload-library", str(artifact), CONTROLLER]

        out = args.output / "simulation"
        try:
            suite.main(["--source-root", str(args.vm_source), "--runtime", str(args.runtime),
                        "--mujoco", str(args.mujoco), "--openssl-root", str(args.openssl_root),
                        "--vendor-model", str(args.vendor_model), "--vendor-assets", str(args.vendor_assets),
                        "--platform-targets", str(registry), "--audit-calls", "--output", str(out)],
                       compile_guest=compile_guest, guest_name="AssemblyScript+WAT", guest_widths=(32,),
                       guest_inputs=(Path(__file__), source, artifact, sidecar, sdk / "bin/wras",
                                     sdk / "language/as/driver.py", sdk / "language/as/compile.mjs"))
        finally:
            compiled = out / "compiled-model/physics.mjb"
            if compiled.is_file():
                (out / "compiled-model.sha256").write_text(sha(compiled) + "\n")
                compiled.unlink()
        shutil.copyfile(source, args.output / source.name)


if __name__ == "__main__":
    main()
