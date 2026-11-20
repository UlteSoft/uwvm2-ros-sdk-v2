"""@brief Replay Gonum scalar tests through the signed TinyGo SDK and ROSv2 VM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys

from separate_compilation import Profile, cgroup_record, inspect, sha


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "fc402bc485e3a92f8d4f1f0ee5a49e2edf232ed2"
SOURCES = {
    "scalar.go": "2de1d1bb5ba04334294dc116c8ea9b6af07c9eb1d04890056534c4e1bd4f9e8d",
    "scalar_test.go": "b9bcd3cae5ecbd87ab73ec1125b75f120e9b1246289c4115e4fa79e9bb08212b",
    "LICENSE": "b44d9e394ba3efc15de4e5a8ebd843bd8d6325f6ffbb0a4ff6db7181aa15dda3",
}
TESTS = ("TestEqualsRelative", "TestEqualsULP", "TestNaNWith", "TestNaNPayload",
         "TestRound", "TestRoundEven", "TestSame")
PROFILE = Profile(32, "3.0", False, True, "eh")


def main():
    """@brief Verify source identities and run native, guest and denied ABI cases."""
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("input", "site", "vm", "output"):
        parser.add_argument("--" + key, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--platform", default="unitree")
    args = parser.parse_args()
    if ".tmp" not in args.output.parts:
        parser.error("choose a fresh SDK .tmp output directory")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("supply the full SDK commit")
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for name, digest in SOURCES.items():
        if sha(args.input / name) != digest:
            raise ValueError("upstream source differs: " + name)

    out = args.output
    out.mkdir()
    result = {"complete": False, "sdk_commit": args.commit, "cgroup": group, "platform": args.platform,
              "upstream_commit": UPSTREAM, "upstream_files": SOURCES, "upstream_tests": TESTS,
              "vm_sha256": sha(args.vm), "site_sha256": sha(args.site), "cases": []}

    def save():
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")

    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("GO", "UWVM_", "WROS_"))}
    env.update(PATH="/usr/bin:/bin", TMPDIR=str(out), LC_ALL="C", PYTHONDONTWRITEBYTECODE="1",
               GOPROXY="off", GOSUMDB="off", GOTOOLCHAIN="local", GOWORK="off", CGO_ENABLED="0",
               GOCACHE=str(out / "go-cache"), GOMODCACHE=str(out / "go-modules"))

    def run(label, command, *, cwd=out, expected_error=None):
        proc = subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, timeout=300)
        output = proc.stdout + proc.stderr
        (out / (label + ".log")).write_bytes(output)
        passed = (proc.returncode == 0 if expected_error is None else
                  proc.returncode != 0 and expected_error in output)
        result["cases"].append({"name": label, "exit": proc.returncode, "passed": passed,
                                "log_sha256": hashlib.sha256(output).hexdigest()})
        save()
        print(label, proc.returncode, flush=True)
        if not passed:
            raise ValueError(label + " failed. See " + str(out / (label + ".log")))
        return proc.stdout

    install = json.loads(run("install", [sys.executable, "-I", "-B", ROOT / "install/bootstrap.py",
        "install", "--local-repository", ROOT, "--commit", args.commit, "--platform", args.platform,
        "--language", "tinygo", "--prefix", out / "installed", "--site-profile", args.site,
        "--", "--component", "development"]))
    sdk = Path(install["directory"])
    toolchain = Path(json.loads(args.site.read_bytes())["toolchain"])
    host_go = toolchain / "libexec/wros/go/bin/go"
    scalar = out / "gonum-scalar"
    scalar.mkdir()
    for name in SOURCES:
        shutil.copyfile(args.input / name, scalar / name)
    (scalar / "go.mod").write_text("module gonum.org/v1/gonum/floats/scalar\n\ngo 1.24\n")

    tests = (scalar / "scalar_test.go").read_text()
    if tuple(re.findall(r"(?m)^func (Test\w+)\(", tests)) != TESTS or tests.count('"testing"') != 1:
        raise ValueError("unexpected pinned upstream test layout")
    native = run("native", [host_go, "test", "-p", "4", "-count=1", "-v", "."], cwd=scalar)
    if any(b"--- PASS: " + name.encode() + b" " not in native for name in TESTS):
        raise ValueError("native runner did not exercise all upstream tests")

    body = tests.replace('"testing"', '"gonum.org/v1/gonum/floats/scalar/testshim"')
    (scalar / "wros_replay.go").write_text(body)
    shim = scalar / "testshim"
    shim.mkdir()
    (shim / "testing.go").write_text('''package testing
type T struct { Calls int }
func (t *T) Parallel() { t.Calls++ }
func (t *T) Errorf(_ string, _ ...interface{}) { panic("Gonum scalar assertion failed") }
''')
    project = out / "application"
    project.mkdir()
    (project / "go.mod").write_text(
        "module wros.local/gonum-replay\n\ngo 1.24\n\n"
        "require (\n gonum.org/v1/gonum/floats/scalar v0.0.0\n wros.local/scene v0.0.0\n)\n"
        "replace gonum.org/v1/gonum/floats/scalar => ../gonum-scalar\n"
        "replace wros.local/scene => " + json.dumps(str(sdk / "language/tinygo/scene")) + "\n")
    (project / "main.go").write_text(
        'package main\nimport (\n "gonum.org/v1/gonum/floats/scalar"\n'
        ' "gonum.org/v1/gonum/floats/scalar/testshim"\n "wros.local/scene"\n)\n'
        'func main() {\n t := &testing.T{}\n'
        + "".join(" scalar." + test + "(t)\n" for test in TESTS)
        + f' if t.Calls != {len(TESTS)} {{ panic("upstream test count differs") }}\n'
        ' if scene.Abi() != 2 { panic("unexpected ROSv2 version") }\n}\n')

    wasm = out / "gonum-ros.wasm"
    run("wrtg", [sdk / "bin/wrtg", project, "--build-receipt", "-o", wasm])
    receipt_path = Path(str(wasm) + ".wros-build.json")
    run("verify", [sys.executable, "-B", sdk / "install/qualification.py", "--artifact", wasm,
                   "--receipt", receipt_path, "--vm", args.vm, "--approved-receipt-sha256", sha(receipt_path)])
    receipt = json.loads(receipt_path.read_bytes())
    if receipt["mode"] != "strict" or receipt["profile"] != PROFILE.to_dict():
        raise ValueError("expected the signed WasmMTE, wasm32, Core 3.0 EH profile")
    imports = inspect(wasm.read_bytes())
    expected = [{"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}]
    if imports != expected:
        raise ValueError("unexpected guest imports")
    result.update(imports=imports, guest_sha256=sha(wasm),
                  guest_tests_sha256=hashlib.sha256(body.encode()).hexdigest())
    ros = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
    for engine in ("int", "aot"):
        vm = [args.vm, *PROFILE.uwvm_feature_flags(), "--runtime-memtag-mode", "sync",
              "--runtime-" + engine, "--runtime-compile-threads", "0", "--wasm-set-main-module-name", "main",
              "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit", *ros]
        run(engine, [*vm, "--ros-scene-interface", "robot", "abi", "allow", "--run", wasm])
        run(engine + "-hidden", [*vm, "--run", wasm], expected_error=b"ROS scene interface is hidden")
    result["complete"] = True
    save()


if __name__ == "__main__":
    main()
