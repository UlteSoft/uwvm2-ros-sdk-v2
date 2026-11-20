"""@file mujoco_matrix.py
@brief Replay signed installed SDK controllers on digest-pinned MuJoCo models.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
MODEL_LIMIT = 512
JVM_LANGUAGES = {"java", "kotlin"}
LANGUAGES = {"d", "nim", "objectc", "py", "ruby", "rs", "tinygo", "fortran", "zig"} | JVM_LANGUAGES


def sha(path):
    """@brief Measure an exact input or receipt."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def plan(path):
    """@brief Resolve selected local inputs and check the model/platform pairing."""
    data = json.loads(path.read_bytes())
    if not isinstance(data, list) or not 1 <= len(data) <= 4096:
        raise ValueError("expected a nonempty list of simulation rows")
    selections = {}
    for row in data:
        key = (row["platform"], row["language"], row["address_bits"])
        platform, language, bits = key
        if (not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", platform)
                or language not in LANGUAGES or type(bits) is not int or bits not in (32, 64)
                or (language in JVM_LANGUAGES and bits != 32)
                or key in selections):
            raise ValueError("invalid or duplicate simulation selection")
        model, assets, site = (path.parent / row[field] for field in ("model", "assets", "site"))
        limit = row.get("compiled_model_mib", 64)
        model_bytes = model.read_bytes()
        profile = json.loads(model_bytes)
        if (hashlib.sha256(model_bytes).hexdigest() != row["model_sha256"] or profile["platform"] != platform
                or type(limit) is not int or not 1 <= limit <= MODEL_LIMIT
                or not assets.is_dir() or not site.is_file()):
            raise ValueError(f"invalid model inputs for {platform}")
        selections[key] = (model_bytes, assets, site.read_bytes(), limit)
    return selections


def execute(args, key, selection, evidence, env, vm_digest, controller_cache):
    """@brief Install one signed selection and verify the six independent scenarios."""
    platform, language, bits = key
    model_bytes, assets, site_bytes, limit = selection
    evidence.mkdir()
    model = evidence / "model.json"
    site = evidence / "site.json"
    model.write_bytes(model_bytes)
    site.write_bytes(site_bytes)
    with tempfile.TemporaryDirectory(dir=evidence, prefix="work-") as tmp:
        scratch = Path(tmp)
        environ = dict(env, TMPDIR=tmp)

        def run(label, command):
            log = evidence / (label + ".log")
            with log.open("xb") as stdout:
                proc = subprocess.run(list(map(str, command)), cwd=ROOT, env=environ,
                                      stdout=stdout, stderr=subprocess.STDOUT, timeout=1200)
            if proc.returncode:
                raise RuntimeError(f"{label} exited {proc.returncode}")
            return log

        install = run("install", [sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
            "--local-repository", ROOT, "--commit", args.commit, "--platform", platform,
            "--language", language, "--prefix", scratch / "install", "--site-profile", site,
            "--", "--component", "development"])
        installed = json.loads(install.read_bytes())["directory"]
        simulated = evidence / "simulation"
        jvm = language in JVM_LANGUAGES
        runner = "jvm_mujoco.py" if jvm else "mujoco_guest.py"
        compiler_args = (["--sdk", installed, "--controller-cache", controller_cache] if jvm else
                         ["--address-bits", bits, "--installed-sdk", installed])
        try:
            run("driver", [sys.executable, "-B", ROOT / "tests" / runner, "--runtime", args.runtime,
                "--vm-source", args.vm_source, "--mujoco", args.mujoco, "--openssl-root", args.openssl_root,
                "--language", language, *compiler_args,
                "--vendor-model", model, "--vendor-assets", assets, "--vendor-model-max-mib", limit,
                "--output", simulated])
        finally:
            compiled = simulated / "compiled-model/physics.mjb"
            if compiled.is_file():
                (evidence / "compiled-model.sha256").write_text(sha(compiled) + "\n")
                compiled.unlink()
    receipt_path = simulated / "results.json"
    receipt = json.loads(receipt_path.read_bytes())
    required = {f"{platform}-{mode}-{bits}-0-{engine}"
                for mode in ("success", "range", "crash") for engine in ("int", "aot")}
    cases = receipt["cases"]
    if (receipt["complete"] is not True or receipt["runtime_sha256"] != vm_digest
            or receipt["tls"] is not True or receipt["vendor_model"] != json.loads(model_bytes)
            or receipt["guest_language"] != language or len(cases) != len(required)
            or {case["name"] for case in cases if case.get("passed") is True} != required):
        raise ValueError("invalid or incomplete simulation receipt")
    result = dict(status="passed", receipt=str(receipt_path.relative_to(args.output)),
                  receipt_sha256=sha(receipt_path), model_sha256=sha(model), site_sha256=sha(site),
                  cases=sorted(required))
    if jvm:
        permissions = simulated / "driver-permissions.json"
        denial = json.loads(permissions.read_bytes())
        expected = {"compile", "int", "aot"}
        cases = denial["cases"]
        if (denial["complete"] is not True or len(cases) != len(expected)
                or {case["name"] for case in cases if case["status"] == 0} != expected):
            raise ValueError("invalid or incomplete JVM permission receipt")
        result["permissions_sha256"] = sha(permissions)
    return result


def main():
    """@brief Run every planned selection and retain exact per-row evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for name in ("plan", "runtime", "vm-source", "mujoco", "openssl-root", "output"):
        parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
    args = parser.parse_args()
    group = cgroup_record()
    rows = plan(args.plan)
    args.output.mkdir(parents=True)
    vm_digest = sha(args.runtime)
    result = dict(complete=False, passed=False, sdk_commit=args.commit, plan_sha256=sha(args.plan),
                  vm_sha256=vm_digest, cgroup=group, rows={})
    env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1", LC_ALL="C")

    def save():
        temp = args.output / "results.pending"
        temp.write_text(json.dumps(result, indent=2) + "\n")
        temp.replace(args.output / "results.json")

    save()
    with tempfile.TemporaryDirectory(dir=args.output, prefix="jvm-cache-") as cache:
        for key, selection in rows.items():
            name = "-".join(map(str, key))
            evidence = args.output / name
            try:
                row = execute(args, key, selection, evidence, env, vm_digest, cache)
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
                row = dict(status="failed", reason=str(error), evidence=name)
            result["rows"][name] = row
            save()
            print(name, row["status"], flush=True)
    result["complete"] = True
    result["passed"] = all(row["status"] == "passed" for row in result["rows"].values())
    save()
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
