"""Exercise an installed C++ compiler frontend and its post-link import policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("frontend", "toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    options = parser.parse_args()
    work = options.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    source = work / "caller.cpp"
    wasm = work / "body.wasm"
    results = []

    def run(label, cmd, expected):
        result = subprocess.run(list(map(str, cmd)), cwd=work, capture_output=True, timeout=120)
        results.append(dict(label=label, argv=list(map(str, cmd)), exit=result.returncode,
                            stderr=result.stderr.decode(errors="replace")[-3000:]))
        (work / "results.json").write_text(json.dumps(results, indent=2))
        if (result.returncode == 0) != expected:
            raise RuntimeError(f"{label}: {results[-1]}")
        return result.stderr

    command = [options.frontend.resolve(), "--toolchain", options.toolchain.resolve(),
               "--sysroots", options.sysroots.resolve(), "--reactor", "--export", "_start",
               "-O3", "-g", "-o", wasm, source]
    source.write_text('#include <wros/scene.h>\nextern "C" void _start() { if (wr_abi() != 2) __builtin_trap(); }\n')
    run("authorized-abi", command, True)
    original = hashlib.sha256(wasm.read_bytes()).hexdigest()
    for module, name in [("wasi_snapshot_preview1", "sock_shutdown"), ("wasi_snapshot_preview1", "path_open"),
                         ("uwvm_ros_v2", "abi"), ("unregistered", "read")]:
        # The two-argument signature intentionally mismatches the zero-argument ROS abi.
        source.write_text(f'extern "C" __attribute__((import_module("{module}"), import_name("{name}"))) '
                          'unsigned foreign(unsigned, unsigned);\n'
                          'extern "C" void _start() { if (foreign(1, 2)) __builtin_trap(); }\n')
        error = run(module + "." + name, command, False)
        if b"unauthorized import or signature" not in error or hashlib.sha256(wasm.read_bytes()).hexdigest() != original:
            raise RuntimeError(f"failed link policy or replaced output for {module}.{name}")
    for engine in ("int", "aot"):
        run("accepted-output-" + engine, [options.runtime.resolve(), "--wasm-set-main-module-name", "main",
            "--runtime-" + engine, "--runtime-llvm-jit-cache-path", "disable", "--ros-scene-create", "robot",
            "--ros-scene-bind", "robot", "main", "--ros-scene-interface", "robot", "abi", "allow",
            "--run", wasm], True)
    print("Verified authorized execution and four atomic post-link refusals")


if __name__ == "__main__":
    main()
