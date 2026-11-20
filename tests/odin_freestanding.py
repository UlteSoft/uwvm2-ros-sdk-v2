"""Exercise installed Odin development projects with the actual SDK backend and VM."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from platform_projects import passed_engines
from separate_compilation import cgroup_record, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import Source, install
from imports import Reader, inspect, require_core

ABI = {"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}


def main():
    """Build the installed Xmake projects and check permission and MTE modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--platform", action="append")
    parser.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    for label in ("tagged-toolchain", "tagged-sysroots", "plain-toolchain", "plain-sysroots", "xmake", "vm", "output"):
        parser.add_argument("--" + label, required=True, type=Path)
    args = parser.parse_args()
    source = Source(args.commit, ROOT)
    platforms = args.platform or list(json.loads((ROOT / "share/targets.json").read_text())["platforms"])
    args.output.mkdir(mode=0o700)
    evidence = {"commit": args.commit, "target": args.target, "cgroup": cgroup_record(), "platforms": {}}

    def run(label, command, cwd, env, refused=None):
        proc = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=120)
        log = args.output / (label + ".log")
        log.write_bytes(proc.stdout)
        expected = proc.returncode == 0 if refused is None else proc.returncode != 0 and refused in proc.stdout
        if not expected:
            raise ValueError(f"unexpected command exit {proc.returncode}. See {log}")
        return proc.stdout.decode(errors="replace")

    def memory_flags(path):
        reader = Reader(path.read_bytes())
        require_core(reader)
        while reader.position < len(reader.data):
            section = reader.byte()
            content = reader.take(reader.uint())
            if section == 5:
                limits = Reader(content)
                assert limits.uint() == 1
                return limits.uint()
        raise ValueError("missing memory section")

    expected_flags = 5 if args.target == "wasm64" else 1
    for platform in platforms:
        with tempfile.TemporaryDirectory(dir=args.output) as scratch:
            work = Path(scratch)
            source.requested.clear()
            record = install(source, platform, "odin", work / "sdk", [])
            root = Path(record["directory"])
            selected = source.requested.copy()
            assert "third-parties/odin/source.tar.xz" not in selected
            assert all(p.startswith("language/odin/") for p in selected if p.startswith("language/"))
            assert all(p.startswith("platform/" + platform + "/") for p in selected if p.startswith("platform/"))
            projects = root / "examples/platform" / platform
            env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(root), WROS_VM=str(args.vm),
                       XMAKE_GLOBALDIR=str(work / "xmake"), WROS_TOOLCHAIN=str(args.tagged_toolchain),
                       WROS_SYSROOTS=str(args.tagged_sysroots))
            checks = {}
            for case in ("common", "migration"):
                project = projects / case / "odin"
                run(platform + "-" + case + "-configure",
                    [args.xmake, "f", "-a", args.target, "-c", "-y"], project, env)
                run(platform + "-" + case + "-build", [args.xmake, "build", "-j1"], project, env)
                result = run(platform + "-" + case + "-test", [args.xmake, "test", "-j1"], project, env)
                artifact, = list((project / "build").rglob("*.wasm"))
                assert inspect(artifact.read_bytes()) == ([ABI] if case == "common" else [])
                assert memory_flags(artifact) == expected_flags
                checks[case] = {"engines": passed_engines(result, [artifact]), "sha256": sha(artifact)}
                if not evidence["platforms"] and case == "common":
                    disasm = run("tagged-disassembly", [args.tagged_toolchain / "bin/llvm-objdump", "-d", artifact],
                                 work, env)
                    assert "memtag.release" in disasm and any(op in disasm for op in ("memtag.claim", "memtag.reserve"))
                    sections = run("debug-sections", [args.tagged_toolchain / "bin/llvm-objdump", "-h", artifact], work, env)
                    assert ".debug_line" in sections
            if not evidence["platforms"]:
                common = projects / "common/odin/controller.odin"
                wrodin = root / "bin/wrodin"
                runner = root / "tools/xmake/run_guest.py"
                output = work / "application.wasm"
                plain = [wrodin, common, "--target", args.target, "--toolchain", args.plain_toolchain, "--sysroots", args.plain_sysroots,
                         "--no-mte", "--ros-abi", "--build-receipt", "-o", output]
                run("untagged-build", plain, work, env)
                proof = json.loads(output.with_suffix(".wasm.wros-build.json").read_text())
                assert proof["mode"] == "off" and proof["profile"]["mte"] is False and proof["artifact_sha256"] == sha(output)
                assert proof["profile"]["address_bits"] == int(args.target[4:])
                assert memory_flags(output) == expected_flags
                disasm = run("untagged-disassembly", [args.plain_toolchain / "bin/llvm-objdump", "-d", output], work, env)
                assert "memtag." not in disasm
                for engine in ("int", "aot"):
                    launch = [sys.executable, runner, output, args.target, "3.0", "single",
                              "--disable-tags", "--engine", engine]
                    run("untagged-" + engine, [*launch, "--queries", "abi"], work, env)
                    run("untagged-refuse-" + engine, launch, work, env, b"ROS scene interface is hidden")
                    tagged, = list((common.parent / "build").rglob("*.wasm"))
                    run("tagged-refuse-" + engine,
                        [sys.executable, runner, tagged, args.target, "3.0", "single", "--check-tags", "--engine", engine],
                        work, env, b"ROS scene interface is hidden")
                rejected = work / "rejected.wasm"
                default = [wrodin, common, "--target", args.target, "--toolchain", args.tagged_toolchain,
                           "--sysroots", args.tagged_sysroots, "-o", rejected]
                run("undeclared-abi", default, work, env, b"must import precisely the selected ROSv2 ABI")
                assert not rejected.exists()
                bogus = work / "undeclared.odin"
                entry = common.read_text()
                bogus.write_text(entry.replace('foreign import ros "uwvm_ros_v2"', 'foreign import ros "unexpected"'))
                run("unknown-import", [wrodin, bogus, *default[2:], "--ros-abi"], work, env,
                    b"unauthorized import or signature unexpected.abi")
                assert not rejected.exists()
                bogus.write_text(entry.replace('start :: proc "c" () {', 'start :: proc "c" (_: i32) {'))
                run("wrong-entry", [wrodin, bogus, *default[2:], "--ros-abi"], work, env,
                    b"must define _start() -> ()")
                assert not rejected.exists()
                other = "wasm64" if args.target == "wasm32" else "wasm32"
                run("reject-pseudo-memory64", [*default, "--target", "wasm64p32"], work, env, b"invalid choice")
                run("wrong-width-sysroot", [*default, "--target", other], work, env, b"no sysroot built by this compiler")
                assert not rejected.exists()
                if args.target == "wasm64":
                    pointer = ROOT / "tests/odin/memory64.odin"
                    for enabled, tools, sysroots in ((True, args.tagged_toolchain, args.tagged_sysroots),
                                                    (False, args.plain_toolchain, args.plain_sysroots)):
                        mode = "on" if enabled else "off"
                        artifact = work / ("width-" + mode + ".wasm")
                        flags = [] if enabled else ["--no-mte"]
                        run("width-build-" + mode,
                            [wrodin, pointer, "--target", "wasm64", "--toolchain", tools, "--sysroots", sysroots,
                             *flags, "-o", artifact], work, env)
                        assert inspect(artifact.read_bytes()) == [] and memory_flags(artifact) == 5
                        run_flag = "--check-tags" if enabled else "--disable-tags"
                        for engine in ("int", "aot"):
                            run("width-" + mode + "-" + engine,
                                [sys.executable, runner, artifact, "wasm64", "3.0", "single", run_flag, "--engine", engine],
                                work, env)
                    checks["memory64"] = ["tagged-int", "tagged-aot", "untagged-int", "untagged-aot"]

                plan = install(source, platform, "odin", work / "source-sdk",
                               ["--component", "compiler-source"], plan=True)
                assert "odin/compiler-source" in plan["packages"] and "compiler-source" not in plan["packages"]
                checks["additional"] = ["default-mte", "debug-line", "untagged-build", "untagged-int", "untagged-aot",
                                        "no-grant-refusal", "undeclared-abi-refusal", "unknown-import-refusal",
                                        "entry-signature-refusal", "wrong-width-sysroot-refusal", "pseudo-memory64-refusal", "source-selection"]
            evidence["platforms"][platform] = {"checks": checks, "transfer_paths": selected}
            (args.output / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
            print(platform, "common and migration passed INT/AOT", flush=True)
    evidence["complete"] = True
    (args.output / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
