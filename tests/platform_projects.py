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
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    """@brief Return the SHA-256 of the exact artifact supplied to the next stage."""
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def main():
    """@brief Build and run selected positive examples and verify assertion failures on request."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", action="append", default=[])
    p.add_argument("--language", required=True)
    p.add_argument("--case", dest="kinds", choices=("common", "extension", "migration"), action="append")
    p.add_argument("--component", default="development")
    p.add_argument("--commit", required=True)
    for name in ("vm", "xmake", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--site", type=Path)
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
    state = {"complete": False, "sdk_commit": a.commit, "vm_sha256": digest(vm), "cgroup": cgroup,
             "language": a.language, "site_sha256": digest(a.site) if a.site else None, "cases": []}

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
            run(case+"-configure", [xmake,"f","-p","wasm-wasip1","-a","wasm32","-y"], project)
            run(case+"-build", [xmake,"build","-j1"], project)
            modules = sorted((project/"build").rglob("*.wasm"))
            if not modules:
                raise RuntimeError(case+" produced no Wasm")
            log = run(case+"-test", [xmake,"test","-j1"], project)
            for engine in ("int","aot"):
                if "/"+engine not in log:
                    raise RuntimeError(case+" did not register an "+engine+" test")
            if "0 test(s) failed" not in log:
                raise RuntimeError(case+" did not report a successful guest test suite")
            state["cases"][-1]["modules"] = {m.name:digest(m) for m in modules}
            save()
            if a.check_failure and kind == "common" and a.language == "c":
                sensor = project/"sensor.c"
                code = sensor.read_text()
                if "!= 407" not in code:
                    raise RuntimeError("missing local negative-control fixture")
                sensor.write_text(code.replace("!= 407","!= 408",1))
                log = run(case+"-failed-assertion", [xmake,"test","-j1","sensor/*"], project, fail=True)
                if "failed" not in log.lower() or "unreachable" not in log.lower():
                    raise RuntimeError("expected a failing guest assertion")
    state["complete"] = True
    save()


if __name__ == "__main__":
    main()
