"""Build actual VB.NET and exercise its typed scene import in both VM engines."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from imports import inspect


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("sdk", "runtime", "dotnet", "mono-compiler", "toolchain", "xmake", "output"):
        parser.add_argument("--" + key, required=True, type=lambda p: Path(p).resolve())
    args = parser.parse_args()
    membership = Path("/proc/self/cgroup").read_text().strip().split("::", 1)[1]
    group = Path("/sys/fs/cgroup") / membership.lstrip("/")
    if ((group / "memory.max").read_text().strip(), (group / "memory.swap.max").read_text().strip()) != ("68719476736", "0"):
        parser.error("the existing 64 GiB qualification cgroup is required")
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    project = out / "project"
    shutil.copytree(args.sdk / "examples/vbnet/scene-abi", project)
    compiler = args.sdk / "bin/wrvb"
    fixture = project / "Robot.vb"
    env = dict(os.environ, WROS_DOTNET=str(args.dotnet), WROS_MONO=str(args.mono_compiler),
               WROS_TOOLCHAIN=str(args.toolchain), UWVM_ROS_SDK_ROOT=str(args.sdk), WROS_PLATFORM="unitree",
               PATH="/usr/bin:/bin:" + os.environ["PATH"], TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, cgroup=membership, vm=digest(args.runtime), compiler=digest(compiler),
                  source=digest(fixture), cases=[], modules={})

    def run(label, argv, success=True):
        result = subprocess.run(argv, cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        (out / (label + ".log")).write_bytes(result.stdout)
        report["cases"].append(dict(name=label, exit=result.returncode, argv=list(map(str, argv))))
        (out / "results.json").write_text(json.dumps(report, indent=2))
        if (result.returncode == 0) != success:
            raise ValueError(f"unexpected result for {label}, see {out / (label + '.log')}")
        return result.stdout

    run("configure", [args.xmake, "f", "-c", "-y", "-a", "wasm32"])
    run("xmake", [args.xmake, "-r"])
    artifact, = project.glob("build/**/robot.wasm")
    common = [compiler, "--dotnet", args.dotnet, "--mono-compiler", args.mono_compiler, "--toolchain", args.toolchain]
    direct = out / "direct.wasm"
    run("wrvb", [*common, "--scene-entry", "Robot.Start", fixture, "-o", direct])
    for name, module in (("cli", direct), ("xmake", artifact)):
        imports = inspect(module.read_bytes())
        if imports != [dict(module="uwvm_ros_v2", name="abi", kind=0, params=[], results=["i32"])]:
            raise ValueError(f"unexpected Visual Basic imports {imports}")
        report["modules"][name] = digest(module)
        for engine in ("int", "aot"):
            base = [args.runtime, *Profile().uwvm_feature_flags(), "--debug-fault-action", "exit", "--runtime-" + engine,
                    "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main"]
            bind = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main", "--ros-scene-interface", "robot", "abi"]
            for action, flags in (("hidden", []), ("deny", [*bind, "deny"]), ("allow", [*bind, "allow"])):
                run(name + "-" + engine + "-" + action, [*base, *flags, "--run", module], action == "allow")

    bad = project / "Storage.vb"
    bad.write_text("Public NotInheritable Class Storage\n    Public Shared slot As Integer\n"
                   "    Public Shared Function Read(value As Integer) As Integer\n"
                   "        Return slot Xor value\n    End Function\nEnd Class\n")
    rejected = out / "rejected.wasm"
    run("refuse-storage", [*common, "--entry", "Storage.Read", bad, "-o", rejected], False)
    inherited = project / "Inherited.vb"
    inherited.write_text("Public Class Ancestor\nEnd Class\nPublic NotInheritable Class Child\n"
                         "    Inherits Ancestor\n    Public Shared Function Pass(value As Integer) As Integer\n"
                         "        Return value\n    End Function\nEnd Class\n")
    run("refuse-managed-base", [*common, "--entry", "Child.Pass", inherited, "-o", rejected], False)
    if rejected.exists():
        raise ValueError("rejected source produced an artifact")
    report["complete"] = True
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
