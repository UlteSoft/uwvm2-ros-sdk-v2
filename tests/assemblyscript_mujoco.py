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
CARRIER_PARAMS = ["i64", "i32", "i64", "i64", "i64", "i64", "i64"]


def driver_payload(suite, deadline, mode):
    """@brief Encode the frozen canonical joint request shared by both guest routes."""
    prefix = suite.u64(1) * 6 + suite.profile("simulation.position") + suite.profile("simulation.radian.logical")
    prefix += suite.text("simulation.joint") + suite.text("le64")
    target = suite.u64(0x4000000000000000 if mode == "range" else 0x3fe0000000000000)
    payload = prefix + suite.blob(target) + suite.u64(0) * 2 + suite.u64(deadline)
    data = suite.u64(1) + suite.u64(deadline) + suite.blob(payload)
    return data, 24 + len(prefix) + 8


def render_guest(suite, deadline, mode, count):
    """@brief Marshal the controller's scalar result into the bounded driver request."""
    g = suite.Fixture(suite.NAMES, 32, 0)
    cap = g.open("joint")
    g.extra_imports.append(f'(import "{CONTROLLER}" "jointTarget" '
                           '(func $jointTarget (param i64 i32) (result f64)))')
    g.globals.add("sequence")
    data, target = driver_payload(suite, deadline, mode)
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
    g.write(request + target,
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


def render_direct(suite, source, deadline, mode, count):
    """@brief Generate scalar assignments without requiring a managed array or data segment."""
    data, target = driver_payload(suite, deadline, mode)
    prelude = (f"const STEPS:u64={count};\nconst TARGET:u32={target};\n"
               f"const MODE:i32={SCENARIOS[mode]};\nconst REQUEST_BYTES:u32={len(data)};\n"
               "function stageRequest(): void {\n")
    for offset in range(0, len(data), 8):
        chunk = data[offset:offset + 8]
        if len(chunk) == 8:
            prelude += f"    writeWord({offset}, {int.from_bytes(chunk, 'little')});\n"
        else:
            prelude += "".join(f"    writeByte({offset + i}, {value});\n" for i, value in enumerate(chunk))
    return source.read_text() + "\n" + prelude + "}\n"


def main():
    """@brief Install one exact SDK selection and qualify the mixed-language simulation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("vm-source", "runtime", "mujoco", "openssl-root", "vendor-model", "vendor-assets", "output"):
        parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--vendor-model-max-mib", type=int, default=64)
    parser.add_argument("--direct-driver", action="store_true")
    parser.add_argument("--no-mte", action="store_true")
    args = parser.parse_args()
    if not __debug__:
        parser.error("simulation qualification requires Python assertions")
    if not 1 <= args.vendor_model_max_mib <= 512:
        parser.error("the compiled model limit must be between 1 and 512 MiB")
    if args.no_mte and not args.direct_driver:
        parser.error("--no-mte applies to the direct driver replay")
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
        source = ROOT / "tests/mujoco" / ("assemblyscript_driver.ts" if args.direct_driver else "controller.ts")
        artifact = args.output / "controller.wasm"
        sidecar = artifact.with_suffix(".wasm.wros-as.json")
        guest_inputs = [Path(__file__), source, sdk / "bin/wras", sdk / "language/as/driver.py",
                        sdk / "language/as/compile.mjs"]
        if args.direct_driver:
            guest_inputs += [sdk / "language/as/driver_lowering.mjs", sdk / "language/as/wros.ts"]
        else:
            with (args.output / "controller-build.log").open("xb") as log:
                subprocess.run([sdk / "bin/wras", source, "--build-receipt", "-g", "-o", artifact], env=env,
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
            receipt = json.loads(sidecar.read_bytes())
            data = artifact.read_bytes()
            assert receipt["mte_requested"] is True and receipt["linear_memories"] == 0
            assert receipt["source_sha256"] == sha(source) and receipt["wasm_sha256"] == sha(artifact)
            assert inspect(data) == [] and all(data[start] not in (5, 11, 12) for start, _, _, _ in sections(data))
            guest_inputs += [artifact, sidecar]

        def expected_import(name, params):
            return {"module": "uwvm_ros_v2", "name": name, "kind": 0, "params": params, "results": ["i32"]}

        def compile_guest(wasm, width, deadline, mode, count, run):
            assert width == 32
            names = [name for name in suite.NAMES if name != "driver.describe" or mode == "crash"]
            policy = ["--wasip1-single-create", "main", "--wasip1-single-disable", "main"]
            if args.direct_driver:
                app = wasm.with_suffix(".ts")
                app.write_text(render_direct(suite, source, deadline, mode, count))
                flags = [arg for name in ["capability.open", *names] for arg in ("--ros-operation", name)]
                run(wasm.stem + "-compile", [sdk / "bin/wras", app, "--ros-driver", "--build-receipt", "-g",
                    *(["--no-mte"] if args.no_mte else []), *flags, "-o", wasm], env=env)
                proof = json.loads(wasm.with_suffix(".wasm.wros-as.json").read_bytes())
                assert proof["mte_requested"] is not args.no_mte and proof["linear_memories"] == 1
                assert proof["wasm_sha256"] == sha(wasm) and proof["source_sha256"] == sha(app)
                expected = [expected_import("capability.open", ["i32", "i64", "i64", "i64"]),
                            *(expected_import(name, CARRIER_PARAMS) for name in names)]
                assert sorted(inspect(wasm.read_bytes()), key=lambda entry: entry["name"]) == sorted(
                    expected, key=lambda entry: entry["name"])
                return [*policy, "-WF3", *(
                    ["--wasm-feature-disable-memtag-extension"] if args.no_mte else ["--runtime-memtag-mode", "sync"])]
            wat = wasm.with_suffix(".wat")
            wat.write_text(render_guest(suite, deadline, mode, count))
            run(wasm.stem + "-assemble", ["wat2wasm", "--enable-multi-memory", "--debug-names", wat, "-o", wasm],
                env=env)
            imports = inspect(wasm.read_bytes())
            expected = [{"module": CONTROLLER, "name": "jointTarget", "kind": 0,
                         "params": ["i64", "i32"], "results": ["f64"]}]
            for name, params in [(name, CARRIER_PARAMS) for name in suite.NAMES] + [
                    ("capability.open", ["i32", "i64", "i64", "i64"])]:
                expected.append(expected_import(name, params))
            assert imports == expected
            return [*policy, "--wasip1-single-create", CONTROLLER, "--wasip1-single-disable", CONTROLLER,
                    "--wasm-preload-library", str(artifact), CONTROLLER]

        out = args.output / "simulation"
        try:
            suite.main(["--source-root", str(args.vm_source), "--runtime", str(args.runtime),
                        "--mujoco", str(args.mujoco), "--openssl-root", str(args.openssl_root),
                        "--vendor-model", str(args.vendor_model), "--vendor-assets", str(args.vendor_assets),
                        "--vendor-model-max-mib", str(args.vendor_model_max_mib),
                        "--platform-targets", str(registry), "--audit-calls", "--output", str(out)],
                       compile_guest=compile_guest, guest_name="AssemblyScript" if args.direct_driver else "AssemblyScript+WAT",
                       guest_widths=(32,), guest_inputs=guest_inputs)
        finally:
            compiled = out / "compiled-model/physics.mjb"
            if compiled.is_file():
                (out / "compiled-model.sha256").write_text(sha(compiled) + "\n")
                compiled.unlink()
        shutil.copyfile(source, args.output / source.name)


if __name__ == "__main__":
    main()
