"""Build from a fixed-commit signed JVM installation and execute both build products."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from separate_compilation import cgroup_record, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "vm", "xmake", "site", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--language", choices=("java", "kotlin"), required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    cgroup = cgroup_record()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, TMPDIR=str(out), XMAKE_GLOBALDIR=str(out / "xmake-global"), PYTHONDONTWRITEBYTECODE="1")
    for variable in ("WROS_TOOLCHAIN", "WROS_SYSROOTS", "WROS_JVM_BUNDLE", "UWVM_ROS_SDK_ROOT"):
        env.pop(variable, None)
    language = args.language
    report = dict(complete=False, cgroup=cgroup, language=language, commit=args.commit,
                  vm_sha256=sha(args.vm), site_sha256=sha(args.site), cases=[], products={})

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, *, cwd=out, negative=None):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, timeout=350)
        logs = result.stdout + result.stderr
        passed = result.returncode == 0 if negative is None else result.returncode != 0 and negative in logs
        (out / (name + ".log")).write_bytes(logs)
        report["cases"].append(dict(name=name, exit=result.returncode, passed=passed,
                                    log_sha256=hashlib.sha256(logs).hexdigest()))
        save()
        if not passed:
            raise RuntimeError(name + ": " + logs[-1200:].decode(errors="replace"))
        return result.stdout

    save()
    install = [sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install", "--commit", args.commit,
               "--local-repository", args.repository.resolve(), "--platform", "unitree", "--language", language]
    site = json.loads(args.site.read_bytes())
    wrong = out / "wrong-release.json"
    wrong.write_text(json.dumps(site | {"release_sha256": "0"*64}))
    run("reject-wrong-release", [*install, "--prefix", out/"denied", "--site-profile", wrong],
        negative=("exactly one signed synchronous " + language + " release").encode())
    selected = json.loads(run("install", [*install, "--prefix", out/"install", "--site-profile", args.site.resolve()]))
    sdk = Path(selected["directory"])
    example = sdk / "examples" / language / "synchronous-aot"
    project = out / "project"
    shutil.copytree(example, project)
    env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_PLATFORM="unitree")
    report["sdk"] = str(sdk)
    command, source = ("wrjava", "Main.java") if language == "java" else ("wrkt", "Main.kt")
    guest = out / "control.wasm"
    cli = [sdk/"bin"/command, "--main-class", "example.Main", project/source, "-o", guest]
    run("cli", cli)
    previous = sha(guest)
    run("reject-unapproved-bundle", [*cli, "--bundle", out], negative=b"explicit bundle differs from the signed JVM site")
    assert sha(guest) == previous
    run("xmake-configure", [args.xmake.resolve(), "f", "-c", "-y", "-a", "wasm32"], cwd=project)
    run("xmake-build", [args.xmake.resolve(), "-j1", "robot"], cwd=project)
    built, = (project/"build").rglob("robot.wasm")
    for producer, product in (("cli", guest), ("xmake", built)):
        assert inspect(product.read_bytes()) == [{"module":"uwvm_ros_v2","name":"abi","kind":0,"params":[],"results":["i32"]}]
        report["products"][producer] = {"path":str(product), "sha256":sha(product)}
        for engine in ("int", "aot"):
            vm = [args.vm.resolve(), *Profile().uwvm_feature_flags(), "--runtime-" + engine, "--debug-fault-action", "exit",
                  "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                  "--runtime-memtag-mode", "sync", "--wasm-set-main-module-name", "main"]
            run(producer+"-"+engine+"-hidden", [*vm, "--run", product], negative=b"ROS scene interface is hidden")
            run(producer+"-"+engine+"-granted", [*vm, "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                "--ros-scene-interface", "robot", "abi", "allow", "--run", product])
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
