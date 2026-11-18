"""Sign a local toolchain release with a disposable WSEA authority and exercise the installed SDK."""
import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import ROOT, Profile, cgroup_record, inspect, sha
from test_core_abi import COMPONENT, fn_import


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("unsigned", "toolchain", "sysroots", "runtime", "cosign", "vm-source", "output", "authority-work"):
        parser.add_argument("--" + key, type=lambda path: Path(path).resolve(), required=True)
    parser.add_argument("--xmake", type=Path, help="exercise an installed language project using this operator-provided Xmake")
    parser.add_argument("--objc-clang", type=Path)
    parser.add_argument("--objc-runtime", type=Path)
    parser.add_argument("--producer", type=Path, help="WROS Nim lowering binary")
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--sdk-commit", required=True)
    parser.add_argument("--address-bits", type=int, choices=(32, 64), default=32)
    parser.add_argument("--language", choices=("c", "cpp", "lua", "nim", "objectc", "fortran"), default="c")
    parser.add_argument("--eh", action="store_true", help="use the default EH-enabled frontend configuration")
    parser.add_argument("--fortran-lapack", type=lambda path: Path(path).resolve(), nargs=2, metavar=("DLAPY3", "DLADIV"),
                        help="check the two original corpus subprograms using the signed Fortran installation")
    parser.add_argument("--fortran-default", action="store_true",
                        help="exercise the Fortran frontend's default optimization, symbols and exception ABI")
    a = parser.parse_args()
    if a.fortran_lapack and (a.language != "fortran" or not a.xmake):
        parser.error("--fortran-lapack requires the Fortran installation/Xmake test")
    if a.fortran_default and a.language != "fortran":
        parser.error("--fortran-default is specific to the Fortran installation test")
    if (a.producer is not None) != (a.language == "nim"):
        parser.error("--producer is required for Nim")
    if a.language in ("nim", "lua", "fortran") and not a.eh:
        parser.error("this language release requires the EH sysroot")
    if a.language == "objectc" and (not a.objc_clang or not a.objc_runtime):
        parser.error("supply --objc-clang and --objc-runtime for Objective-C")
    if a.xmake and a.language not in ("lua", "nim", "objectc", "fortran"):
        parser.error("--xmake requires a published example project for this language")
    if not a.output.is_relative_to(ROOT / ".tmp"):
        parser.error("use a new SDK .tmp directory")
    if not a.authority_work.is_relative_to(a.vm_source / ".tmp"):
        parser.error("use a new VM .tmp directory under protected WSEA ancestors for the test CA")
    os.umask(0o077)
    a.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    a.authority_work.mkdir(mode=0o700, parents=True, exist_ok=False)
    important = [a.unsigned, a.runtime, a.cosign, a.sysroots, Path(__file__)]
    if a.language == "objectc":
        important.extend([a.objc_clang, a.objc_runtime / "runtime.json", a.objc_runtime / "libobjc.a"])
    report = dict(complete=False, cgroup=cgroup_record(), inputs={str(p): sha(p) for p in important}, cases=[])
    env = {**os.environ, "TMPDIR": str(a.output), "PYTHONDONTWRITEBYTECODE": "1"}

    def save():
        (a.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, success=True, directory=None, timeout=90):
        command = list(map(str, argv))
        proc = subprocess.run(command, cwd=directory or a.output, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        (a.output / (name + ".log")).write_bytes(proc.stdout)
        report["cases"].append(dict(name=name, code=proc.returncode, expected_success=success, argv=command))
        save()
        if (proc.returncode == 0) != success:
            raise RuntimeError("unexpected " + name + " result, see " + str(a.output / (name + ".log")))

    run("install-language", [sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install", "--commit", a.sdk_commit,
                      "--local-repository", a.repository.resolve(), "--platform", "unitree", "--language", a.language,
                      "--prefix", a.output / "sdk"])
    installed = json.loads((a.output / "install-language.log").read_bytes())
    sdk = Path(installed["directory"])
    if not sdk.resolve().is_relative_to(a.output / "sdk"):
        raise ValueError("installer selected an unexpected destination")
    if [pkg for pkg in installed["packages"] if pkg.startswith("languages/")] != ["languages/" + a.language]:
        raise ValueError("installer selected a different language")
    fixture = a.vm_source / "test/0073.ros-tests/support/source/security_wsea/algorithm_matrix.py"
    report["inputs"][str(fixture)] = sha(fixture)
    spec = importlib.util.spec_from_file_location("wros_test_authority", fixture)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ca = mod.Fixtures(a.authority_work / "test-authority").pki("site", family="ED25519")
    module_id = "wros.sdk.memory.release"
    policy = a.authority_work / "local.policy"
    run("policy", [a.cosign, "wasm", "secure", "policy-init", "--output", policy, "--state-dir", a.authority_work / "state",
                   "--trust-root", ca["root"], "--certificate", ca["certificate"], "--module-id", module_id,
                   "--algorithms", "Ed25519"])
    signed = a.output / "signed.wasm"
    now = datetime.datetime.now(datetime.timezone.utc)

    def stamp(seconds):
        return (now + datetime.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")

    run("sign", [a.cosign, "wasm", "secure", "sign", a.unsigned, "--policy", policy, "--key", ca["key"],
                 "--certificate", ca["certificate"], "--crl", ca["crl"], "--module-id", module_id, "--module-version", "1",
                 "--algorithm", "Ed25519", "--not-before", stamp(-60), "--not-after", stamp(3600), "--output", signed])
    wasm = a.output / "app.wasm"
    front = sdk / "bin" / {"c": "wrc", "cpp": "wrcc", "lua": "wrlua", "nim": "wrnim", "objectc": "wrobjc", "fortran": "wrf"}[a.language]
    suffix = {"objectc": "m", "fortran": "f90"}.get(a.language, a.language)
    app = a.output / ("app." + suffix)
    def application(value):
        if a.language == "fortran":
            return ("program sampling\nuse iso_c_binding, only: c_int\nimplicit none\n"
                    "interface\nsubroutine fail() bind(c,name=\"abort\")\nend subroutine\nend interface\n"
                    "integer(c_int), allocatable :: sample(:)\ninteger :: rc\n"
                    "allocate(sample(4),stat=rc)\nif(rc/=0) call fail()\n"
                    f"sample={value}\nif(sample(4)/={value}) call fail()\n"
                    "deallocate(sample,stat=rc)\nif(rc/=0) call fail()\nend program\n")
        if a.language == "objectc":
            return ('__attribute__((objc_root_class)) @interface Sample { Class isa; } + (unsigned)value; @end\n'
                    f'@implementation Sample + (unsigned)value {{ return {value}; }} @end\n'
                    f'void _start(void) {{ if ([Sample value] != {value}) __builtin_trap(); }}\n')
        if a.language == "nim":
            return f"let sample = new(int)\nsample[] = {value}\ndoAssert sample[] == {value}\n"
        if a.language == "lua":
            return "local t = {value=" + str(value) + "}; assert(t.value==" + str(value) + ")\n"
        linkage = 'extern "C" ' if a.language == "cpp" else ""
        return "static volatile int n; " + linkage + "void _start(void){ n=" + str(value) + "; if(n!=" + str(value) + ") __builtin_trap(); }\n"
    app.write_text(application(1))
    build = [front, "--toolchain", a.toolchain, "--sysroots", a.sysroots]
    if a.address_bits == 64:
        build += ["--target", "wasm64"]
    if a.language == "nim":
        build.extend(["--producer", a.producer.resolve(), "-O3", "-g"])
    elif a.language == "objectc":
        build.extend(["--objc-clang", a.objc_clang.resolve(), "--objc-runtime", a.objc_runtime.resolve(),
                      "--eh" if a.eh else "--no-eh", "--reactor", "--export", "_start", "-O3", "-g"])
    elif a.language == "fortran":
        if not a.fortran_default:
            build.extend(["--eh", "-O3", "-g"])
    elif a.language != "lua":
        build.extend(([] if a.eh else ["--no-eh"]) + ["--reactor", "--export", "_start"])
    build += ["--build-receipt", app, "-o", wasm]
    run("before-configuration", build, False)
    config = sdk / "share/qualification/local-trust.json"
    trusted = dict(verifier=str(a.cosign), verifier_sha256=sha(a.cosign), policy=str(policy), statement=str(signed), statement_sha256=sha(signed))
    config.write_text(json.dumps(trusted))
    run("default-mte", build)
    run("explicit-mte", [build[0], "--mte", *build[1:]])
    receipt = Path(str(wasm) + ".wros-build.json")
    run("artifact", [sys.executable, sdk / "install/qualification.py", "--artifact", wasm, "--receipt", receipt,
                     "--vm", a.runtime, "--approved-receipt-sha256", sha(receipt)])
    # An approved receipt identifies the bytes presented for deployment. The
    # independent core ABI check also applies when that approval is genuine.
    for label, data, error in (
        ("preview2", fn_import("wasi:clocks/monotonic-clock@0.2.0", "now"), b"prohibited"),
        ("preview3", fn_import("wasi:clocks/monotonic-clock@0.3.0", "now"), b"prohibited"),
        ("component", COMPONENT, b"Component Model binaries are prohibited"),
    ):
        variant = a.output / (label + ".wasm")
        variant.write_bytes(data)
        note = a.output / (label + ".json")
        fields = json.loads(receipt.read_text())
        fields["artifact_sha256"] = sha(variant)
        note.write_text(json.dumps(fields))
        run(label + "-at-deployment", [sys.executable, sdk / "install/qualification.py", "--artifact", variant,
            "--receipt", note, "--vm", a.runtime, "--approved-receipt-sha256", sha(note)], False)
        if error not in (a.output / (label + "-at-deployment.log")).read_bytes():
            raise ValueError("missing deployment ABI rejection diagnostic for " + label)
    app.write_text(application(2))
    run("changed-application", build)
    for engine in ("int", "aot"):
        vm = [a.runtime, *Profile(a.address_bits).uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
              "--runtime-llvm-jit-cache-path", "disable"]
        if a.language in ("lua", "objectc"):
            vm += ["--wasm-set-main-module-name", "main", "--wasip1-single-create", "main", "--wasip1-single-enable",
                   "main", "--wasip1-single-interface", "main", "clock_time_get_wasm64" if a.address_bits == 64 else "clock_time_get", "allow",
                   "--wasip1-single-grant", "main", "realtime-clock"]
        run("changed-application-" + engine, [*vm, "--run", wasm])
    if a.language != "lua":
        expected_imports = {("wasi_snapshot_preview1", "clock_time_get_wasm64" if a.address_bits == 64 else "clock_time_get")} if a.language == "objectc" else set()
        if {(v["module"], v["name"]) for v in inspect(wasm.read_bytes())} != expected_imports:
            raise ValueError("standalone language fixture has unexpected imports")
        linkage = 'extern "C" ' if a.language == "cpp" else ""
        if a.language == "fortran":
            app.write_text((sdk / "examples/fortran/body.f90").read_text())
        elif a.language == "nim":
            app.write_text("import wros_scene\ndoAssert wr_abi()==2\n")
        else:
            app.write_text('#include <wros/scene.h>\n' + linkage +
                           'void _start(void){if(wr_abi()!=2) __builtin_trap();}\n')
        run("ros-only-build", build)
        ros_imports = {(v["module"], v["name"]) for v in inspect(wasm.read_bytes())}
        required = {("uwvm_ros_v2", "abi")}
        if ros_imports not in (required, required | expected_imports):
            raise ValueError("unexpected imports in ROS-only application")
        for engine in ("int", "aot"):
            vm = [a.runtime, *Profile(a.address_bits).uwvm_feature_flags(), "--runtime-" + engine, "--runtime-compile-threads", "0",
                  "--runtime-llvm-jit-cache-path", "disable", "--wasm-set-main-module-name", "main"]
            if a.language == "objectc" and ros_imports != required:
                vm += ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                       "--wasip1-single-interface", "main", next(iter(expected_imports))[1], "allow",
                       "--wasip1-single-grant", "main", "realtime-clock"]
            name = "ros-only-denied-" + engine
            run(name, [*vm, "--run", wasm], False)
            if b"ROS scene interface is hidden" not in (a.output / (name + ".log")).read_bytes():
                raise ValueError("missing ROS permission denial diagnostic")
            run("ros-only-granted-" + engine, [*vm, "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                                               "--ros-scene-interface", "robot", "abi", "allow", "--run", wasm])
    if a.language == "lua":
        run("guest-only", [*build, "--guest-seed", "0"])
        if inspect(wasm.read_bytes()):
            raise ValueError("seeded standalone Lua imported a host interface")
        for engine in ("int", "aot"):
            run("guest-only-" + engine, [a.runtime, *Profile(a.address_bits).uwvm_feature_flags(), "--runtime-" + engine,
                                       "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable", "--run", wasm])
    else:
        run("unapproved-optimization", [*build, "-O0"], False)
    if a.xmake and a.language == "fortran":
        env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_TOOLCHAIN=str(a.toolchain), WROS_SYSROOTS=str(a.sysroots),
                   WROS_VM=str(a.runtime), WROS_RUN_QUERIES="abi", XMAKE_GLOBALDIR=str(a.output / "xmake-global"))
        examples = sdk / "examples/fortran"
        for label, source_dir, directory in (("xmake", examples, a.output),
                                              ("xmake-archive", examples / "static", a.output / "archive-project")):
            directory.mkdir(exist_ok=True)
            project = (source_dir / "xmake.lua").read_text()
            if a.fortran_default:
                project = project.replace('    set_symbols("debug")\n', "")
            (directory / "xmake.lua").write_text(project)
            for source in source_dir.glob("*.f90"):
                (directory / source.name).write_bytes(source.read_bytes())
            run(label + "-configure", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1",
                                      "-a", "wasm" + str(a.address_bits)], directory=directory)
            run(label + "-build", [a.xmake.absolute(), "-j1", "robot"], directory=directory)
            run(label + "-run", [a.xmake.absolute(), "run", "robot"], directory=directory)
        archive_build = a.output / "archive-project/build"
        archive, = archive_build.rglob("*.a")
        app_with_library, = archive_build.rglob("robot.wasm")
        calls = [(item["module"], item["name"]) for item in inspect(app_with_library.read_bytes())]
        if not archive.read_bytes().startswith(b"!<arch>\n") or calls != [("uwvm_ros_v2", "abi")]:
            raise ValueError("unexpected linked Fortran archive output or imports")
        if a.fortran_lapack:
            run("signed-ros-lapack", [sys.executable, "-B", ROOT / "tests/fortran_archives.py",
                "--toolchain", a.toolchain, "--sysroots", a.sysroots, "--runtime", a.runtime, "--sdk", sdk,
                "--address-width", a.address_bits, *(["--no-debug"] if a.fortran_default else []),
                "--dlapy3", a.fortran_lapack[0], "--dladiv", a.fortran_lapack[1],
                "--output", a.output / "signed-ros-lapack"], timeout=600)
    elif a.xmake and a.language == "objectc":
        env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_TOOLCHAIN=str(a.toolchain), WROS_SYSROOTS=str(a.sysroots),
                   WROS_OBJC_CLANG=str(a.objc_clang.resolve()), WROS_OBJC_RUNTIME=str(a.objc_runtime.resolve()),
                   WROS_VM=str(a.runtime), WROS_RUN_QUERIES="abi,realtime-clock", XMAKE_GLOBALDIR=str(a.output / "xmake-global"))
        (a.output/"xmake.lua").write_text((sdk/"examples/objectc/xmake.lua").read_text())
        (a.output/"body.m").write_text((sdk/"examples/objectc/body.m").read_text())
        run("xmake-configure", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm"+str(a.address_bits)])
        run("xmake-build", [a.xmake.absolute(), "-j1", "robot_status"])
        run("xmake-run", [a.xmake.absolute(), "run", "robot_status"])
    elif a.xmake and a.language == "nim":
        env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_TOOLCHAIN=str(a.toolchain), WROS_SYSROOTS=str(a.sysroots),
                   WROS_NIM_PRODUCER=str(a.producer.resolve()), WROS_VM=str(a.runtime), WROS_RUN_QUERIES="abi",
                   XMAKE_GLOBALDIR=str(a.output / "xmake-global"))
        project = a.output / "xmake.lua"
        project.write_text((sdk / "examples/nim/xmake.lua").read_text().replace("body.nim", "app.nim"))
        run("xmake-configure", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm" + str(a.address_bits)])
        run("xmake-build", [a.xmake.absolute(), "-j1", "robot"])
        run("xmake-run", [a.xmake.absolute(), "run", "robot"])
    elif a.xmake:
        env.update(UWVM_ROS_SDK_ROOT=str(sdk), WROS_TOOLCHAIN=str(a.toolchain), WROS_SYSROOTS=str(a.sysroots),
                   WROS_VM=str(a.runtime), XMAKE_GLOBALDIR=str(a.output / "xmake-global"), WROS_RUN_QUERIES="")
        app.write_text("local a,b=math.randomseed(); assert(a==37 and b==0)\n")
        project = a.output / "xmake.lua"
        project.write_text('includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))\n'
                           'target("seeded")\n  set_kind("binary")\n  set_language("lua")\n  set_ros_platform("unitree")\n'
                           '  set_wros_profile({lua_seed=37})\n  add_files("app.lua")\ntarget_end()\n')
        run("xmake-configure", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm" + str(a.address_bits)])
        run("xmake-build", [a.xmake.absolute(), "-j1", "seeded"])
        run("xmake-run", [a.xmake.absolute(), "run", "seeded"])
        guard_operations = ("capability.open", "capability.close", "guard.create", "guard.trigger", "guard.take")
        select = "add_wros_lua_operations(" + ", ".join(json.dumps(op) for op in guard_operations) + ")"
        project.write_text(project.read_text().replace('add_files("app.lua")', select + '\n  add_files("app.lua")'))
        app.write_bytes((sdk / "examples/lua/guard.lua").read_bytes())
        run("xmake-guard-configure", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm" + str(a.address_bits)])
        run("xmake-guard-build", [a.xmake.absolute(), "-j1", "seeded"])
        artifact, = (a.output / "build").rglob("seeded.wasm")
        if {(v["module"], v["name"]) for v in inspect(artifact.read_bytes())} != {("uwvm_ros_v2", op) for op in guard_operations}:
            raise ValueError("incorrect imports in installed Xmake guard build")
        policy = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]
        for op in guard_operations:
            policy += ["--ros-scene-interface", "robot", op, "allow"]
        policy += ["--ros-scene-grant", "robot", "signal", "guard", "signal", "local", "guard.create,guard.trigger,guard.take"]
        for engine in ("int", "aot"):
            run("xmake-guard-" + engine, [a.runtime, *Profile(a.address_bits).uwvm_feature_flags(),
                "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                "--wasm-set-main-module-name", "main", *policy, "--run", artifact])
        project.write_text(project.read_text().replace("lua_seed=37", "lua_seed=4294967296"))
        run("xmake-invalid-seed", [a.xmake.absolute(), "f", "-c", "-y", "-p", "wasm-wasip1", "-a", "wasm" + str(a.address_bits)], False)
    authentic = signed.read_bytes()
    signed.write_bytes(a.unsigned.read_bytes())
    config.write_text(json.dumps(dict(trusted, statement_sha256=sha(signed))))
    run("unsigned", build, False)
    changed = bytearray(authentic)
    start = changed.index(b'"language":"' + a.language.encode() + b'"')
    changed[start + len('"language":"')] = ord("z")
    signed.write_bytes(changed)
    config.write_text(json.dumps(dict(trusted, statement_sha256=sha(signed))))
    run("altered", build, False)
    signed.write_bytes(authentic)
    config.write_text(json.dumps(dict(trusted, statement_sha256="0" * 64)))
    run("unapproved-signed-release", build, False)
    config.write_text(json.dumps(dict(trusted, verifier_sha256="0" * 64)))
    run("verifier-replaced", build, False)
    config.unlink()
    run("trust-removed", build, False)
    report["complete"] = all(sha(Path(path)) == digest for path, digest in report["inputs"].items())
    save()
    if not report["complete"]:
        raise ValueError("WSEA fixture input changed")


if __name__ == "__main__":
    main()
