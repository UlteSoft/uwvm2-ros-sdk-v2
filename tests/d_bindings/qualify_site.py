"""Exercise a measured BetterC pipeline and emit a candidate WSEA bundle for independent signing."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "language/d"))
from driver import build
from release import FORMAT, PROFILE, SETTINGS, c_release, canon, digest, host_files, local_release, measure
from imports import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--toolchain", type=Path, required=True)
    p.add_argument("--measure-host", action="store_true", help="print the host closure for operator review and exit")
    for name in ("c-site", "vm", "output"):
        p.add_argument("--" + name, type=Path)
    for name in ("sdk-commit", "approved-host-sha256", "approved-c-release-sha256"):
        p.add_argument("--" + name)
    opt = p.parse_args()
    tc = opt.toolchain.resolve(strict=True)
    if opt.measure_host:
        host = host_files(tc)
        print(json.dumps({"sha256": canon(host), "inputs": host}, indent=2))
        return
    if not all((opt.c_site, opt.vm, opt.output, opt.sdk_commit, opt.approved_host_sha256, opt.approved_c_release_sha256)):
        p.error("qualification needs an approved C site, host identity, full SDK commit, VM and fresh output")
    head = subprocess.check_output(["git", "-C", SDK, "rev-parse", "HEAD"], text=True).strip()
    if head != opt.sdk_commit or subprocess.check_output(["git", "-C", SDK, "status", "--porcelain"]):
        p.error("select a clean checkout at the approved commit")
    site = local_release.parse_site(opt.c_site.read_bytes())
    rows = local_release.verified_releases(site["trust"])
    manifests = list(map(Path, site["sysroots"]))
    inputs = measure(tc, manifests)
    if canon(inputs["host"]) != opt.approved_host_sha256:
        p.error("the D compiler closure differs from the operator-approved inventory")
    base = c_release(rows, opt.approved_c_release_sha256, inputs["backend"])
    if digest(opt.vm) != base["vm_sha256"]:
        p.error("the VM differs from its signed C qualification")
    marker = (tc / "bin/wros-flang-mte").resolve(strict=True)
    marker_info = json.loads(marker.with_name(marker.name + ".json").read_bytes())
    if marker_info["source_sha256"] != digest(SDK / "language/fortran/mark_mte.cpp"):
        p.error("the LLVM marker differs from this SDK's reviewed recipe")
    out = opt.output.resolve()
    if not out.is_relative_to(SDK / ".tmp"):
        p.error("use a fresh SDK .tmp directory")
    out.mkdir(parents=True, exist_ok=False)
    evidence = {}
    wasm = out / "qualified.wasm"
    source = SDK / "examples/d/body.d"
    with tempfile.TemporaryDirectory(dir=out) as temp:
        build(source, wasm, tc, manifests, Path(temp), evidence)
    imported = inspect(wasm.read_bytes())
    if imported != [{"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}]:
        raise ValueError("unexpected imports in the D probe")
    cases = {}
    for engine in ("int", "aot"):
        controls = [opt.vm, *PROFILE.uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
                    "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main",
                    "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
        trials = []
        for name, grant, expected in (("deny", [], 127), ("grant", ["--ros-scene-interface", "robot", "abi", "allow"], 0)):
            cmd = [*controls, *grant, "--run", wasm]
            result = subprocess.run(cmd, capture_output=True, timeout=90)
            log = out / (engine + "-" + name + ".log")
            log.write_bytes(result.stdout + result.stderr)
            if result.returncode != expected or (name == "deny" and b"scene interface is hidden" not in log.read_bytes()):
                raise ValueError(engine + " failed the " + name + " check")
            trials.append({"action": name, "exit": result.returncode, "log": digest(log), "artifact": digest(wasm)})
        cases[engine] = trials
        evidence["vm-" + engine] = canon(trials)
    contract = json.loads((SDK / "share/abi/ros.json").read_bytes())
    declarations = (SDK / "language/d/wros_scene.d").read_text().splitlines()
    expected = []
    for op in contract["operations"]:
        params = op["wasm_signature"]["parameters"]
        if op["wasm_signature"]["results"] != ["i32"] or set(params) - {"i32", "i64"}:
            raise ValueError("unexpected VM ABI shape")
        name = "wros_" + op["name"].replace(".", "_").replace("-", "_")
        args = ", ".join(("uint" if t == "i32" else "ulong") + " a" + str(i) for i,t in enumerate(params))
        expected.append("uint " + name + "(" + args + ");")
    if [line for line in declarations if line.startswith("uint ")] != expected:
        raise ValueError("D binding declarations differ from the VM ABI")
    evidence["bindings"] = canon(expected)
    row = {"format": FORMAT, "language": "d", "sdk_commit": head, "profile": PROFILE.to_dict(), "settings": SETTINGS,
           "inputs": inputs, "c_release_sha256": canon(base), "vm_sha256": base["vm_sha256"], "evidence": evidence}
    (out / "release.json").write_text(json.dumps(row, indent=2) + "\n")
    (out / "unsigned.wasm").write_bytes(local_release.encode([base, row]))
    (out / "results.json").write_text(json.dumps({"complete": True, "source": digest(source), "bindings": len(expected),
                                                "imports": imported, "row": canon(row), "trials": cases}, indent=2) + "\n")


if __name__ == "__main__":
    main()
