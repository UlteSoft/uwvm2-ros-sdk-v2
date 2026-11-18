"""Build, run and refuse guest targets from exact, separately installed selections."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys

from separate_compilation import cgroup_record, inspect, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "toolchain", "sysroots", "no-mte-sysroots", "vm", "xmake", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--flang", type=Path)
    parser.add_argument("--flang-mte-tool", type=Path)
    parser.add_argument("--goroot", type=Path)
    parser.add_argument("--tinygoroot", type=Path)
    args = parser.parse_args()
    work = args.output.resolve()
    record = dict(complete=False, cgroup=cgroup_record(), commit=args.commit, cases=[], modules={})
    work.mkdir(parents=True, exist_ok=False)
    tmp = work / "tmp"
    tmp.mkdir()
    env = dict(os.environ, TMPDIR=str(tmp), WROS_TOOLCHAIN=str(args.toolchain.resolve()),
               WROS_SYSROOTS=str(args.sysroots.resolve()), WROS_SYSROOTS_NO_MTE=str(args.no_mte_sysroots.resolve()), WROS_VM=str(args.vm.resolve()),
               XMAKE_GLOBALDIR=str(work / "global"), WROS_PLATFORM="unitree", WROS_RUN_QUERIES="")
    os.environ["TMPDIR"] = str(tmp)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    xmake = str(args.xmake.resolve())
    record["inputs"] = {str(p): sha(p) for p in (args.vm, args.sysroots, args.no_mte_sysroots, args.toolchain / "bin/clang",
                        args.xmake, Path(__file__))}
    for lang, plat in (("c", "unitree"), ("cpp", "abb"), ("lua", "unitree")):
        selection = install(Source(args.commit, args.repository.resolve()), plat, lang, work / "sdk", [])
        env["SELECTION_" + lang.upper()] = selection["directory"]
    env["UWVM_ROS_SDK_ROOT"] = env["SELECTION_C"]

    def save():
        (work / "results.json").write_text(json.dumps(record, indent=2) + "\n")

    def run(name, cwd, command, error=None, **extra):
        proc = subprocess.run(list(map(str, command)), cwd=cwd, env={**env, **extra},
                              capture_output=True, timeout=180)
        log = proc.stdout + proc.stderr
        (work / (name + ".log")).write_bytes(log)
        record["cases"].append(dict(name=name, exit=proc.returncode, error_expected=error))
        save()
        if (proc.returncode == 0) != (error is None) or (error and error.encode() not in log):
            raise RuntimeError(name + ": " + log.decode(errors="replace")[-1500:])
        print(name, flush=True)

    demo = work / "demo"
    shutil.copytree(Path(env["SELECTION_C"]) / "examples/c", demo)
    for arch in ("wasm32", "wasm64"):
        run("configure-" + arch, demo, [xmake, "f", "-c", "-y", "-a", arch])
        run("build-" + arch, demo, [xmake, "-j1", "robot"])
        module = next(demo.glob("build/*/" + arch + "/*/robot.wasm"))
        rows = inspect(module.read_bytes())
        if [(r["module"], r["name"]) for r in rows] != [("uwvm_ros_v2", "abi")]:
            raise AssertionError(rows)
        record["modules"][arch] = dict(path=str(module), sha256=sha(module), imports=rows)
        run("run-zero-" + arch, demo, [xmake, "run", "robot"], "ROS scene interface is hidden")
        run("run-granted-" + arch, demo, [xmake, "run", "robot"], WROS_RUN_QUERIES="abi")
    run("reject-local-query", demo, [xmake, "run", "robot"], "WROS_RUN_QUERIES accepts",
        WROS_RUN_QUERIES="unregistered")

    for label, edit, error in (
        ("missing-platform", 'set_ros_platform("abb")', "Platform is not installed"),
        ("missing-language", 'set_language("java")', "Language is not installed"),
        ("invalid-profile", 'set_wros_profile({budget=4})', "Unknown WROS profile field"),
        ("host-link", 'add_links("pthread")', "Unsupported guest target setting"),
    ):
        directory = work / label
        shutil.copytree(Path(env["SELECTION_C"]) / "examples/c", directory)
        script = directory / "xmake.lua"
        script.write_text(script.read_text().replace("target_end()", edit + "\ntarget_end()"))
        run(label, directory, [xmake, "f", "-c", "-y"], error)

    explicit_off = work / "explicit-off"
    shutil.copytree(Path(env["SELECTION_C"]) / "examples/c", explicit_off)
    project = explicit_off / "xmake.lua"
    project.write_text(project.read_text().replace("target_end()", "set_wros_profile({mte=false})\ntarget_end()"))
    run("configure-off", explicit_off, [xmake, "f", "-c", "-y"])
    run("missing-off-closure", explicit_off, [xmake, "-j1", "robot"], "no sysroot built by this compiler",
        WROS_SYSROOTS_NO_MTE=str(args.sysroots.resolve()))
    run("build-off", explicit_off, [xmake, "-j1", "robot"])
    run("run-off", explicit_off, [xmake, "run", "robot"], WROS_RUN_QUERIES="abi")
    multi = work / "multi"
    multi.mkdir()
    (multi / "measure.c").write_text("int measure(int x){return x+DELTA;}\n")
    (multi / "body.cpp").write_text('#include <wros/scene.h>\nextern "C" int measure(int);\n'
        'extern "C" void _start(){if(wr_abi()!=2 || measure(40)!=42) __builtin_trap();}\n')
    (multi / "xmake.lua").write_text('''
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("measure")
    set_kind("static")
    set_language("c")
    set_ros_platform("unitree")
    add_defines("DELTA=2")
    add_files("measure.c")
target_end()
target("body")
    set_kind("binary")
    set_language("cpp")
    set_ros_platform("abb")
    set_wros_sdk(os.getenv("SELECTION_CPP"))
    set_wros_profile({std="c++20"})
    add_deps("measure")
    add_files("body.cpp")
target_end()
''')
    run("two-selection-configure", multi, [xmake, "f", "-c", "-y"])
    run("two-selection-build", multi, [xmake, "-j1", "body"])
    run("two-selection-run", multi, [xmake, "run", "body"], WROS_RUN_QUERIES="abi")

    lua = work / "lua"
    lua.mkdir()
    (lua / "body.lua").write_text("assert(wros.abi() == 2 and table.concat({1, 2}) == '12')\n")
    (lua / "xmake.lua").write_text('''
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("script")
    set_kind("binary")
    set_language("lua")
    set_ros_platform("unitree")
    set_wros_sdk(os.getenv("SELECTION_LUA"))
    set_wros_profile({lua_abi=true})
    add_files("body.lua")
target_end()
''')
    run("lua-configure", lua, [xmake, "f", "-c", "-y"])
    run("lua-build", lua, [xmake, "-j1", "script"])
    run("lua-run", lua, [xmake, "run", "script"], WROS_RUN_QUERIES="abi,realtime-clock")
    for language, inputs in (("fortran", (args.flang, args.flang_mte_tool)), ("tinygo", (args.goroot, args.tinygoroot))):
        if not any(inputs):
            continue
        if not all(inputs):
            parser.error("supply both build inputs for " + language)
        directory = Path(install(Source(args.commit, args.repository.resolve()), "unitree", language, work / "sdk", [])["directory"])
        settings = dict(UWVM_ROS_SDK_ROOT=str(directory))
        if language == "fortran":
            settings.update(WROS_FLANG=str(args.flang.resolve()), WROS_FLANG_MTE_TOOL=str(args.flang_mte_tool.resolve()))
        else:
            settings.update(WROS_GOROOT=str(args.goroot.resolve()), WROS_TINYGOROOT=str(args.tinygoroot.resolve()))
        for mte in (True, False):
            label = language + ("-default" if mte else "-off")
            project = work / label
            project.mkdir()
            if language == "fortran":
                source = "body.f90"
                (project / source).write_text("program robot\nuse wros_scene\nimplicit none\ninteger :: version\nversion = wr_abi()\nend program\n")
            else:
                source = "go.mod"
                (project / source).write_text("module example.local/robot\n\ngo 1.24\n\nrequire wros.local/scene v0.0.0\n"
                    + "replace wros.local/scene => " + json.dumps(str(directory / "language/tinygo/scene")) + "\n")
                (project / "main.go").write_text('package main\nimport "wros.local/scene"\nfunc main(){ if scene.Abi()!=2 { panic("ABI") } }\n')
            (project / "xmake.lua").write_text(
                'includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))\n'
                + 'target("robot")\nset_kind("binary")\nset_ros_platform("unitree")\nset_language("' + language + '")\n'
                + ('set_wros_profile({mte=false})\n' if not mte else '')
                + 'set_symbols("debug")\nset_optimize("fastest")\nadd_files("' + source + '")\ntarget_end()\n')
            run(label + "-configure", project, [xmake, "f", "-c", "-y"], **settings)
            run(label + "-build", project, [xmake, "-j1", "robot"], **settings)
            module = next(project.glob("build/*/wasm32/*/robot.wasm"))
            rows = inspect(module.read_bytes())
            if [(r["module"], r["name"]) for r in rows] != [("uwvm_ros_v2", "abi")]:
                raise AssertionError(rows)
            record["modules"][label] = dict(sha256=sha(module), imports=rows)
            run(label + "-denied", project, [xmake, "run", "robot"], "ROS scene interface is hidden", **settings)
            run(label + "-run", project, [xmake, "run", "robot"], WROS_RUN_QUERIES="abi", **settings)
    record["complete"] = True
    save()


if __name__ == "__main__":
    main()
