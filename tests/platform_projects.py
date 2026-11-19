"""@file platform_projects.py
@brief Install a single approved SDK selection per platform and execute the shipped xmake projects.
@details Pin the SDK commit, VM and site inputs. Run this script inside the test cgroup.
Each result distinguishes the actual platform, language, project, guest digest and VM outcome.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    """@brief Return the SHA-256 of the exact artifact supplied to the next stage."""
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def engine_results(log, modules, outcome):
    """@brief Require a final report with the requested outcome for every guest and engine.
    @param outcome Expected Xmake test status for these guest assertions.
    @param log Output captured from the project's serial Xmake test invocation.
    @param modules Guest modules produced by the materialized project. Its binary
    target names are the Wasm filename stems.
    @return Sorted target/engine names with the expected status in the final report.
    """
    expected = {f"{module.stem}/{engine}" for module in modules for engine in ("int", "aot")}
    if len(expected) != 2 * len(modules):
        raise ValueError("ambiguous guest target names")
    plain = re.sub(r"\x1b\[[0-9;]*m", "", log)
    _, header, report = plain.partition("report of tests:")
    if not header:
        raise ValueError("Xmake did not publish final per-engine results")
    rows = re.findall(r"^\s*\[ *[0-9]+%\]:\s+(\S+)\s+(\S+)", report, re.MULTILINE)
    if len(rows) != len(expected) or {name for name, _ in rows} != expected:
        raise ValueError("Xmake's final tests differ from the expected guest/engine pairs")
    mismatches = [name for name, status in rows if status != outcome]
    if mismatches:
        raise ValueError(f"Xmake expected {outcome} for " + ", ".join(mismatches))
    return sorted(expected)


def passed_engines(log, modules):
    """@brief Return the built guests whose tests passed in both engines."""
    return engine_results(log, modules, "passed")


def main():
    """@brief Build and run selected positive examples and verify assertion failures on request."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", action="append", default=[])
    p.add_argument("--language", required=True)
    p.add_argument("--case", dest="kinds", choices=("common", "extension", "migration"), action="append")
    p.add_argument("--component", default="development")
    p.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32",
                   help="the address width accepted by the selected language and site")
    p.add_argument("--commit", required=True)
    for name in ("vm", "xmake", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--site", type=Path)
    p.add_argument("--managed-host", type=Path, help="prefix created by prepare_host.py for the selected .NET language")
    p.add_argument("--managed-toolchain", type=Path, help="qualified Wasm LLVM installation for .NET AOT")
    p.add_argument("--check-failure", action="store_true", help="also execute a deliberately failing local C assertion")
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    vm = a.vm.resolve(strict=True)
    xmake = a.xmake.resolve(strict=True)
    registry = json.loads((ROOT / "share/targets.json").read_bytes())
    platforms = a.platform or sorted(registry["platforms"])
    if not set(platforms) <= set(registry["platforms"]) or a.language not in registry["languages"]:
        p.error("unknown platform or language")
    cgroup = Path("/proc/self/cgroup").read_text().strip()
    if "docker-af71cb24aa7993383f76ad9c06750b17eb66fd090a2c9ba64b544b19cda9c913.scope" not in cgroup:
        p.error("run in the designated 64 GiB test cgroup")
    env = {k:v for k,v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", WROS_VM=str(vm), TMPDIR=str(out), XMAKE_GLOBALDIR=str(out/"global"))
    if a.language in ("csharp", "fsharp", "vbnet"):
        if a.managed_host is None or a.managed_toolchain is None:
            p.error("a managed example requires --managed-host and --managed-toolchain")
        tools = {"WROS_DOTNET": a.managed_host / "dotnet", "WROS_MONO": a.managed_host / "compiler",
                 "WROS_TOOLCHAIN": a.managed_toolchain}
        for key, directory in tools.items():
            if not directory.is_dir():
                p.error(f"{key} directory is unavailable: {directory}")
            env[key] = str(directory.resolve())
    elif a.managed_host is not None or a.managed_toolchain is not None:
        p.error("managed host parameters apply only to .NET languages")
    state = {"complete": False, "sdk_commit": a.commit, "vm_sha256": digest(vm), "cgroup": cgroup,
             "language": a.language, "target": a.target, "site_sha256": digest(a.site) if a.site else None, "cases": []}

    def save():
        (out/"results.json").write_text(json.dumps(state, indent=2)+"\n")

    def run(name, command, cwd, *, fail=False):
        log = out/(name+".log")
        with log.open("xb") as stream:
            result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=1800)
        state["cases"].append(dict(name=name, status=result.returncode, expected_failure=fail, log_sha256=digest(log)))
        save()
        if (result.returncode != 0) != fail:
            raise RuntimeError(name + ": " + log.read_text(errors="replace")[-1200:])
        return log.read_text(errors="replace")

    for platform in platforms:
        args = [sys.executable, "-I", "-B", ROOT/"install/bootstrap.py", "install", "--local-repository", ROOT,
                "--commit", a.commit, "--platform", platform, "--language", a.language,
                "--prefix", out/"installed"]
        if a.site:
            args.extend(["--site-profile", a.site.resolve(strict=True)])
        args.extend(["--", "--component", a.component])
        result = json.loads(run(platform+"-install", args, out))
        if result["commit"] != a.commit:
            raise RuntimeError("unexpected installed revision")
        sdk = Path(result["directory"])
        env["UWVM_ROS_SDK_ROOT"] = str(sdk)
        for name in result["requested_paths"]:
            if name.startswith("examples/platform/") and name.split("/")[2:5:2] != [platform, a.language]:
                raise RuntimeError("installation fetched an unrelated platform/language example: " + name)
        for kind in a.kinds or ["common", "extension", "migration"]:
            case = platform+"-"+kind
            sample = sdk/"examples/platform"/platform/kind/a.language
            project = out/case
            shutil.copytree(sample, project)
            run(case+"-configure", [xmake,"f","-p","wasm-wasip1","-a",a.target,"-y"], project)
            run(case+"-build", [xmake,"build","-j1"], project)
            modules = sorted((project/"build").rglob("*.wasm"))
            if not modules:
                raise RuntimeError(case+" produced no Wasm")
            log = run(case+"-test", [xmake,"test","-j1"], project)
            state["cases"][-1]["passed_tests"] = passed_engines(log, modules)
            state["cases"][-1]["modules"] = {m.name:digest(m) for m in modules}
            save()
            if a.check_failure and kind == "common" and a.language == "c":
                sensor = project/"sensor.c"
                code = sensor.read_text()
                if "!= 407" not in code:
                    raise RuntimeError("missing local negative-control fixture")
                sensor.write_text(code.replace("!= 407","!= 408",1))
                log = run(case+"-failed-assertion", [xmake,"test","-j1","sensor/*"], project, fail=True)
                if "unreachable" not in log.lower():
                    raise RuntimeError("expected the deliberately failing guest assertion to trap")
                state["cases"][-1]["failed_tests"] = engine_results(log, [Path("sensor.wasm")], "failed")
                save()
    state["complete"] = True
    save()


if __name__ == "__main__":
    main()
