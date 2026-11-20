"""@file sdk_acceptance.py
@brief Execute installed language contracts and scoped platform cases in a test cgroup.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import tempfile

from separate_compilation import ROOT, cgroup_record, sha

from bootstrap import MAX_METADATA, Source, relative
from guest_profile import Profile

CASE_NAMES = ("common", "extension", "migration")
BUNDLED = {"as", "go", "wat"}
MANAGED = {"csharp", "fsharp", "vbnet"}
TOOLS = ("toolchain", "sysroots")
HOSTS = ("managed_host", "managed_toolchain")
PROFILE_PATHS = {"site", *TOOLS, *HOSTS}
INPUT_SCHEMA = "wros-sdk-acceptance-inputs-v1"
RESULT_SCHEMA = "wros-sdk-acceptance-results-v1"
FIXTURE = ROOT / "tests/platform_projects.py"
WAT_PROFILE_TESTS = ("tests/wat_policy.py", "tests/wat_thread_mte.py")
MAX_ARTIFACT = 64 << 20


def hash_bytes(data):
    """@brief Identify a complete staged input exactly."""
    return hashlib.sha256(data).hexdigest()


def read_bytes(path, limit):
    """@brief Snapshot one bounded nonempty input."""
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError(f"{path} must contain between 1 and {limit} bytes")
    return data


def unique_fields(pairs):
    """@brief Reject duplicate keys at every level of the acceptance inputs."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate input field " + key)
        result[key] = value
    return result


def load_inputs(path, platforms, languages):
    """@brief Load exact local sites, managed hosts and artifact identities."""
    if path is None:
        return {}, {}, None
    data = read_bytes(path.resolve(strict=True), MAX_METADATA)
    config = json.loads(data, object_pairs_hook=unique_fields)
    if not isinstance(config, dict) or config.get("schema") != INPUT_SCHEMA or set(config) - {"schema", "profiles", "artifacts"}:
        raise ValueError("invalid acceptance input schema")
    profiles = config.get("profiles", {})
    artifacts = config.get("artifacts", {})
    if not isinstance(profiles, dict) or not isinstance(artifacts, dict):
        raise ValueError("profiles and artifacts must be objects")
    base = path.resolve().parent
    for key, entry in profiles.items():
        scope = key.split("/")
        if scope[-1] not in languages or not (len(scope) == 1 or len(scope) == 2 and scope[0] in platforms):
            raise ValueError("invalid profile selection " + key)
        if not isinstance(entry, dict) or set(entry) - {"target", *PROFILE_PATHS}:
            raise ValueError("invalid profile fields for " + key)
        if entry.get("target", "wasm32") not in ("wasm32", "wasm64"):
            raise ValueError("invalid profile target for " + key)
        paths = PROFILE_PATHS & entry.keys()
        supported = set(HOSTS) if scope[-1] in MANAGED else {"site", *TOOLS}
        if paths - supported or ("site" in paths and paths & set(TOOLS)):
            raise ValueError("choose the prepared managed pair, signed site or explicit tools for " + key)
        if "site" in paths and scope[-1] in {"as", "odin", "wat"}:
            raise ValueError("this profile does not accept a signed site path: " + key)
        for field in paths:
            if not isinstance(entry[field], str) or not entry[field]:
                raise ValueError("expected a local path for " + field + " in " + key)
            entry[field] = (base / entry[field]).absolute()
    for key, entry in artifacts.items():
        scope = key.split("/")
        if len(scope) != 3 or scope[0] not in platforms or scope[1] not in languages or scope[2] not in CASE_NAMES:
            raise ValueError("invalid artifact selection " + key)
        if not isinstance(entry, dict) or set(entry) - {"file", "sha256", "profile", "queries"}:
            raise ValueError("invalid artifact fields for " + key)
        file = entry.get("file")
        digest = entry.get("sha256")
        if not isinstance(file, str) or not file or not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("artifact file and SHA-256 are required for " + key)
        profile = entry.get("profile", {})
        if not isinstance(profile, dict) or set(profile) - set(Profile.__dataclass_fields__):
            raise ValueError("invalid artifact profile for " + key)
        chosen = Profile(**{"exceptions": "noeh", **profile})
        if chosen.wasm_version not in ("1.0", "3.0"):
            raise ValueError("the test runner accepts Core MVP or Core 3.0: " + key)
        entry["profile"] = chosen
        queries = entry.get("queries", [])
        if not isinstance(queries, list) or not all(isinstance(q, str) and "," not in q for q in queries):
            raise ValueError("invalid artifact read-only query list for " + key)
        entry["file"] = (base / file).absolute()
    return profiles, artifacts, hash_bytes(data)


def prereqs(language, metadata, entry):
    """@brief Identify missing local prerequisites for the installed fixture."""
    if not metadata["development_package"]:
        return "development-package-unpublished"
    if language in MANAGED:
        if not all(field in entry and entry[field].is_dir() for field in HOSTS):
            return "prepared-managed-host-and-wasm-toolchain-required"
    elif "site" in entry:
        if not entry["site"].is_file():
            return "site-profile-file-missing"
    elif language == "odin" or any(field in entry for field in TOOLS):
        if not all(field in entry for field in TOOLS) or not entry["toolchain"].is_dir() or not entry["sysroots"].is_file():
            return "explicit-wasm-toolchain-and-sysroots-required"
    elif language not in BUNDLED:
        return "signed-site-profile-required"
    return None


def execute_fixture(row, entry, args, evidence, work):
    """@brief Run the existing exact-commit installer and serial Xmake fixture."""
    destination = work / "fixture"
    command = [sys.executable, "-B", FIXTURE, "--commit", args.commit, "--language", row["language"],
               "--platform", row["platform"], "--case", row["case"], "--target", entry.get("target", "wasm32"),
               "--vm", args.vm, "--xmake", args.xmake, "--output", destination]
    if row["tier"] == "platform":
        # Xmake builds these fresh targets before running their guest tests.
        command.append("--build-via-test")
    if "site" in entry:
        site = work / "site.json"
        site.write_bytes(read_bytes(entry["site"], 32768))
        command.extend(("--site", site))
    for field in (*HOSTS, *TOOLS):
        if field in entry:
            command.extend(("--" + field.replace("_", "-"), entry[field]))
    with (evidence / "fixture.log").open("xb") as transcript:
        process = subprocess.run(list(map(str, command)), cwd=ROOT, stdout=transcript, stderr=subprocess.STDOUT)
    for name in destination.glob("*.log"):
        shutil.copyfile(name, evidence / name.name)
    receipt = destination / "results.json"
    if receipt.is_file():
        shutil.copyfile(receipt, evidence / receipt.name)
    if process.returncode:
        return {"outcome": "blocked", "reason": "installed-fixture-failed", "exit": process.returncode}
    result = json.loads(receipt.read_text())
    test_name = f"{row['platform']}-{row['case']}-test"
    checks = [case for case in result["cases"] if case["name"] == test_name]
    if (not result["complete"] or result["sdk_commit"] != args.commit or result["language"] != row["language"]
            or len(checks) != 1 or checks[0]["status"] != 0):
        raise ValueError("missing complete per-platform fixture evidence")
    modules = checks[0]["modules"]
    engines = checks[0]["passed_tests"]
    expected = {f"{Path(name).stem}/{engine}" for name in modules for engine in ("int", "aot")}
    if not expected or len(engines) != len(expected) or set(engines) != expected:
        raise ValueError("the installed fixture did not confirm both engines for every module")
    return {"outcome": "executable", "modules": modules, "engines": engines,
            "site_sha256": result["site_sha256"]}


def execute_wat_profile(args, platform, source, evidence, work):
    """@brief Qualify the WAT compiler's joint profile once before platform tests."""
    proof = {}
    for path in WAT_PROFILE_TESTS:
        fixture = ROOT / path
        if fixture.read_bytes() != source.read(path, MAX_METADATA):
            raise ValueError("WAT profile test source differs from the selected SDK commit")
        output = work / fixture.stem
        command = [sys.executable, "-B", fixture, "--commit", args.commit, "--platform", platform,
                   "--vm", args.vm, "--output", output]
        if path.endswith("wat_thread_mte.py"):
            command.extend(("--xmake", args.xmake))
        with (evidence / (fixture.stem + ".log")).open("xb") as log:
            process = subprocess.run(list(map(str, command)), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=240)
        retained = evidence / fixture.stem
        retained.mkdir()
        for pattern in ("*.log", "results.json"):
            for item in output.glob(pattern):
                shutil.copyfile(item, retained / item.name)
        if process.returncode:
            return {"outcome": "blocked", "fixture": path, "exit": process.returncode}
        receipt = json.loads((retained / "results.json").read_text())
        if not receipt["complete"] or receipt["commit"] != args.commit or receipt["platform"] != platform:
            raise ValueError("missing exact WAT joint-profile receipt")
        proof[path] = {"checks": len(receipt["checks"]), "result_sha256": sha(retained / "results.json")}
    return {"outcome": "passed", "tests": proof}


def snapshot_runner(source, root):
    """@brief Materialize the exact commit's audited test runner without a compiler install."""
    paths = {"frontend": lambda p: p.startswith("install/"),
             "protocol": lambda p: p == "share/abi/ros.json",
             "xmake/common": lambda p: p == "tools/xmake/run_guest.py"}
    for package, selected in paths.items():
        manifest = json.loads(source.read(f"install/packages/{package}.json", MAX_METADATA))
        for row in manifest["files"]:
            path = relative(row["path"])
            if selected(path):
                data = source.read(path, MAX_METADATA)
                if len(data) != row["bytes"] or hash_bytes(data) != row["sha256"]:
                    raise ValueError("artifact runner file differs from its package manifest: " + path)
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    return root / "tools/xmake/run_guest.py"


def execute_artifact(entry, vm, source, evidence, work):
    """@brief Run the exact supplied module under read-only test policy in both engines."""
    data = read_bytes(entry["file"], MAX_ARTIFACT)
    digest = hash_bytes(data)
    if digest != entry["sha256"]:
        raise ValueError("supplied artifact SHA-256 differs from the selected digest")
    guest = work / "guest.wasm"
    guest.write_bytes(data)
    runner = snapshot_runner(source, work / "runtime")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(WROS_VM=str(vm), PATH="/usr/bin:/bin", TMPDIR=str(work))
    profile = entry["profile"]
    core = "mvp" if profile.wasm_version == "1.0" else profile.wasm_version
    command = [sys.executable, "-I", "-B", runner, guest, f"wasm{profile.address_bits}", core,
               "threads" if profile.threads else "single", "--exceptions", profile.exceptions,
               "--check-tags" if profile.mte else "--disable-tags", "--queries", ",".join(entry.get("queries", []))]
    exits = {}
    for engine in ("int", "aot"):
        with (evidence / (engine + ".log")).open("xb") as log:
            completed = subprocess.run([*command, "--engine", engine], cwd=work, env=env,
                                       stdout=log, stderr=subprocess.STDOUT)
        exits[engine] = completed.returncode
    result = {"guest_sha256": digest, "engine_exit": exits, "profile": profile.to_dict(),
              "queries": entry.get("queries", []), "runner_sha256": sha(runner)}
    if any(exits.values()):
        return {**result, "outcome": "blocked", "reason": "provided-artifact-execution-failed"}
    return {**result, "outcome": "executable"}


def main():
    """@brief Select one language contract and explicit platform example cases."""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--commit", required=True)
    cli.add_argument("--language", action="append")
    cli.add_argument("--platform", action="append")
    cli.add_argument("--contract-platform", help="select the platform used for the once-per-language common example")
    cli.add_argument("--platform-case", action="append", choices=CASE_NAMES,
                     help="default platform cases are extension and migration")
    cli.add_argument("--inputs", type=Path, help="versioned JSON with exact site profiles or supplied Wasm artifacts")
    cli.add_argument("--vm", type=Path)
    cli.add_argument("--xmake", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--plan", action="store_true", help="record selections and known blockers without executing a guest")
    args = cli.parse_args()

    try:
        group = cgroup_record()
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        source = Source(args.commit, ROOT)
        registry = json.loads(source.read("share/targets.json", MAX_METADATA))
        registered_languages = registry["languages"]
        registered_platforms = registry["platforms"]
        languages = sorted(set(args.language or registered_languages))
        platforms = sorted(set(args.platform or registered_platforms))
        contract_platform = args.contract_platform or platforms[0]
        if not set(languages) <= set(registered_languages) or not set([contract_platform, *platforms]) <= set(registered_platforms):
            raise ValueError("unknown language or platform")
        profiles, artifacts, inputs_hash = load_inputs(args.inputs, registered_platforms, registered_languages)
        if not args.plan:
            if args.vm is None or args.xmake is None:
                raise ValueError("--vm and --xmake are required when executing")
            args.vm = args.vm.resolve(strict=True)
            args.xmake = args.xmake.resolve(strict=True)
            if not all(path.is_file() and os.access(path, os.X_OK) for path in (args.vm, args.xmake)):
                raise ValueError("--vm and --xmake require executable files")
        output = args.output.resolve()
        output.mkdir(parents=True, mode=0o700)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        cli.error(str(error))

    inventory = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", "--name-only", args.commit, "--", "examples/platform", *WAT_PROFILE_TESTS], cwd=ROOT,
    ).decode().split("\0")
    shipped = set(inventory)
    cases = list(dict.fromkeys(args.platform_case or ("extension", "migration")))
    state = {
        "schema": RESULT_SCHEMA, "commit": args.commit, "cgroup": group, "plan": args.plan,
        "languages": languages, "platforms": platforms, "contract_platform": contract_platform, "platform_cases": cases,
        "inputs_sha256": inputs_hash, "orchestrator_sha256": sha(Path(__file__)), "fixture_sha256": sha(FIXTURE),
        "vm_sha256": sha(args.vm) if not args.plan else None,
        "xmake_sha256": sha(args.xmake) if not args.plan else None,
        "complete": False, "all_executable": False, "rows": [],
    }

    def save():
        temporary = output / "pending.json"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(output / "results.json")

    save()
    for language in languages:
        meta = json.loads(source.read(f"share/language/{language}.json", MAX_METADATA))
        language_outcome = None
        routes = [("language-contract", contract_platform, "common"),
                  *(("platform", platform, case) for platform in platforms for case in cases)]
        for tier, platform, case in routes:
            key = f"{platform}/{language}"
            entry = profiles.get(key, profiles.get(language, {}))
            artifact = artifacts.get(f"{key}/{case}") if tier == "platform" else None
            project = f"examples/platform/{platform}/{case}/{language}/xmake.lua"
            row = {"tier": tier, "platform": platform, "language": language, "case": case,
                   "mode": "provided-artifact" if artifact else "installed-example",
                   "project": project if project in shipped and not artifact else None,
                   "target": f"wasm{artifact['profile'].address_bits}" if artifact else entry.get("target", "wasm32")}
            reason = prereqs(language, meta, entry) if artifact is None and (project in shipped or tier == "language-contract") else None
            if reason:
                row.update(outcome="blocked", reason=reason)
            elif artifact is None and project not in shipped:
                row.update(outcome="not_exercised", reason="no-shipped-example")
            elif args.plan:
                row.update(outcome="not_exercised", reason="plan-only")
            elif tier == "platform" and artifact is None and language_outcome != "executable":
                row.update(outcome="blocked", reason="language-contract-not-passed")
            else:
                evidence = output / tier / platform / language / case
                evidence.mkdir(parents=True)
                row["evidence"] = str(evidence.relative_to(output))
                try:
                    with tempfile.TemporaryDirectory(dir=output, prefix="case-") as scratch:
                        work = Path(scratch)
                        result = (execute_artifact(artifact, args.vm, source, evidence, work) if artifact
                                  else execute_fixture(row, entry, args, evidence, work))
                        row.update(result)
                        if (tier == "language-contract" and language == "wat" and row["outcome"] == "executable"
                                and set(WAT_PROFILE_TESTS) <= shipped):
                            profile = execute_wat_profile(args, platform, source, evidence, work)
                            row["joint_profile"] = profile
                            if profile["outcome"] != "passed":
                                row.update(outcome="blocked", reason="joint-profile-test-failed")
                except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                    row.update(outcome="blocked", reason="artifact-or-fixture-error", detail=str(error))
            if tier == "language-contract":
                language_outcome = row["outcome"]
                row.setdefault("joint_profile", {"outcome": "not_exercised"})
            state["rows"].append(row)
            if not args.plan:
                save()
    state["complete"] = True
    state["counts"] = dict(Counter(row["outcome"] for row in state["rows"]))
    state["all_executable"] = all(row["outcome"] == "executable" for row in state["rows"])
    state["all_joint_profiles_passed"] = all(row["joint_profile"]["outcome"] == "passed"
                                             for row in state["rows"] if row["tier"] == "language-contract")
    save()
    print(json.dumps(state["counts"], sort_keys=True))
    return 0 if args.plan or state["all_executable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
