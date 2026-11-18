"""Verify selective xmake payloads against a trusted SDK Git commit."""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import MAX_METADATA, Source, install
from separate_compilation import cgroup_record, sha


def configure(xmake, destination, project, platform, language):
    """Load the installed descriptors into a fresh Xmake project for each pair."""
    project.mkdir(parents=True)
    name = {"c": "body.c", "cpp": "body.cpp", "objectc": "body.m", "lua": "body.lua", "rs": "body.rs", "tinygo": "go.mod", "fortran": "body.f90", "nim": "body.nim"}[language]
    script = [
        'set_project("selection")',
        'includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))',
        'target("robot")',
        '    set_kind("binary")',
        '    set_language(' + json.dumps(language) + ')',
        '    set_ros_platform(' + json.dumps(platform) + ')',
        '    add_files(' + json.dumps(name) + ')',
        'target_end()',
    ]
    (project / "xmake.lua").write_text("\n".join(script) + "\n")
    (project / name).write_text("")
    env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(destination),
               XMAKE_GLOBALDIR=str(project.parent / "settings"))
    command = [str(xmake), "f", "-c", "-y"]
    proc = subprocess.run(command, cwd=project, env=env, capture_output=True, timeout=40)
    if proc.returncode:
        raise RuntimeError(f"configure {platform}/{language}: " +
                           (proc.stdout + proc.stderr).decode(errors="replace")[-2000:])
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--xmake", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    controller = cgroup_record()
    xmake = args.xmake.resolve(strict=True)
    source = Source(args.commit, args.repository.resolve())
    registry = json.loads(source.read("share/targets.json", MAX_METADATA))
    active = []
    for language in registry["languages"]:
        meta = json.loads(source.read(f"share/language/{language}.json", MAX_METADATA))
        if meta["development_package"]:
            active.append(language)
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as scratch:
        prefix = Path(scratch)
        os.environ["TMPDIR"] = str(prefix)
        tempfile.tempdir = str(prefix)
        accepted, refused, controls = [], [], []
        for platform in registry["platforms"]:
            for language in registry["languages"]:
                source.requested.clear()
                if language not in active:
                    try:
                        install(source, platform, language, prefix, [])
                    except ValueError as error:
                        if "has not been published" not in str(error):
                            raise
                    else:
                        raise AssertionError(f"unexpectedly installed {platform}/{language}")
                    if source.requested != ["install/revision.py"]:
                        raise AssertionError("unsupported selection retrieved additional files")
                    refused.append([platform, language])
                    continue

                output = install(source, platform, language, prefix, [])
                paths = set(source.requested)
                destination = Path(output["directory"])
                installed = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
                adapters = {f"language/{language}/xmake/adapter.lua", f"platform/{platform}/xmake/platform.lua"}
                if {path for path in installed if path.endswith(("/xmake/adapter.lua", "/xmake/platform.lua"))} != adapters:
                    raise AssertionError(f"wrong adapters in {destination}")
                for path in ("tools/xmake/ros.lua", "tools/xmake/dispatch.lua", "tools/xmake/run_guest.py",
                             "document/en/xmake.md", "document/zh/xmake.md",
                             "document/en/xmake-api-index.md", "document/zh/xmake-api-index.md"):
                    if path not in installed:
                        raise AssertionError("missing xmake input: " + path)
                if any(path.startswith("platform/") and not path.startswith(f"platform/{platform}/")
                       for path in paths | installed):
                    raise AssertionError("foreign platform was requested or installed")
                language_paths = (f"language/{language}/", "language/rust/") if language == "rs" else (f"language/{language}/",)
                if any(path.startswith("language/") and not path.startswith(language_paths)
                       for path in paths | installed):
                    raise AssertionError("foreign language was requested or installed")
                result = configure(xmake, destination, prefix / "projects" / f"{platform}-{language}",
                                   platform, language)
                accepted.append(dict(platform=platform, language=language, files=len(installed),
                                     xmake_configure_exit=result, requested=source.requested.copy()))
                shutil.rmtree(destination)
            print(f"{platform} checked", flush=True)

        # A protocol-only or declarations-only installation cannot be used as
        # an xmake development installation, even alongside a complete one.
        for language, component in (("c", "protocol"), ("rs", "bindings"), ("as", "bindings")):
            source.requested.clear()
            output = install(source, "unitree", language, prefix, ["--component", component])
            destination = Path(output["directory"])
            if (destination / "tools/xmake").exists() or (destination / "bin").exists():
                raise AssertionError("metadata selection unexpectedly installed build tooling")
            controls.append(dict(language=language, component=component, requested=source.requested.copy()))

        for platform, language, reason in (("absent-platform", "c", "unknown platform"),
                                          ("unitree", "absent-language", "unknown language")):
            source.requested.clear()
            try:
                install(source, platform, language, prefix, [], plan=True)
            except ValueError as error:
                if reason not in str(error) or source.requested != ["install/revision.py"]:
                    raise
            else:
                raise AssertionError("unknown identifier produced a plan")

    inputs = {str(p): sha(p) for p in (xmake, ROOT / "install/bootstrap.py", Path(__file__))}
    report = dict(commit=args.commit, cgroup=controller, inputs=inputs, development_languages=active, accepted=accepted,
                  refused=refused, controls=controls, unknown_identifiers_refused=2)
    with args.receipt.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(f"{len(accepted)} installed pairs, {len(refused)} unsupported pairs refused before payload retrieval")


if __name__ == "__main__":
    main()
