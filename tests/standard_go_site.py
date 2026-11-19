"""@brief Sign and qualify an installed standard-Go scalar release with a disposable local authority."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SDK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDK / "language/go"))
from check_site import compiler_inputs
import local_release


def sha(path):
    """@brief Return the SHA-256 of an evidence or executable file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    """@brief Hash a site row or test group using canonical JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    """@brief Check signed installation, guest execution and policy rejection on both engines."""
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("vm", "vm-source", "cosign", "suite", "output", "authority-work"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    protected = args.authority_work.resolve()
    protected.mkdir(mode=0o700, parents=True, exist_ok=False)
    cases = []
    suite = json.loads((args.suite / "results.json").read_bytes())
    if suite["vm_sha256"] != sha(args.vm) or suite["test_sha256"] != sha(SDK / "tests/standard_go.py"):
        raise ValueError("suite uses a different VM or test revision")
    required_artifacts = {"arithmetic", "consumer", "common", "extension", "migration"}
    if set(suite["artifacts"]) != required_artifacts:
        raise ValueError("missing signed evidence inputs")
    by_name = {c["name"]: c for c in suite["cases"]}
    for name in ("int-arithmetic", "aot-arithmetic", "compile-default", "reject-slice", "reject-heap",
                 "common-test", "migration-test", "extension-test", "int-deny", "aot-deny"):
        if (by_name[name]["exit"] == 0) != (not name.startswith("reject-") and not name.endswith("-deny")):
            raise ValueError("a required qualification test did not pass")
    def run(name, argv, success=True):
        path = out / (name + ".log")
        with path.open("wb") as log:
            ret = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=180).returncode
        cases.append(dict(name=name, exit=ret, log_sha256=sha(path)))
        if (ret == 0) != success:
            raise RuntimeError(name + " failed: " + path.read_text(errors="replace")[-1100:])
        return path
    def evidence(names):
        return canonical(dict(suite=sha(args.suite / "results.json"), cases=[by_name[n] for n in names]))
    row = dict(format="wros-go-register-site", language="go", inputs=compiler_inputs(SDK), vm_sha256=sha(args.vm),
               tests=dict(int=evidence(["int-arithmetic", "int-deny"]), aot=evidence(["aot-arithmetic", "aot-deny"]),
                          admission=evidence(sorted(n for n in by_name if n.startswith("reject-"))),
                          xmake=evidence(["common-test", "extension-test", "migration-test"])))
    unsigned = out / "release.wasm"
    unsigned.write_bytes(local_release.encode([row]))
    fixture = args.vm_source / "test/0073.ros-tests/support/source/security_wsea/algorithm_matrix.py"
    spec = importlib.util.spec_from_file_location("wros_test_authority", fixture)
    authority = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(authority)
    now = datetime.datetime.now(datetime.timezone.utc)
    def stamp(seconds):
        return (now + datetime.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory(dir=protected) as temp:
        ca = authority.Fixtures(Path(temp) / "authority").pki("test", family="ED25519")
        # Policy files retain these public certificate paths after the test key is erased.
        public = {}
        for name in ("root", "certificate"):
            public[name] = protected / (name + ".pem")
            shutil.copyfile(ca[name], public[name])
        def sign(name, module_id, source):
            policy = protected / (name + ".policy")
            result = out / (name + "-signed.wasm")
            prefix = [args.cosign, "wasm", "secure"]
            run(name + "-policy", [*prefix, "policy-init", "--output", policy, "--state-dir", protected / (name + "-state"),
                                    "--trust-root", public["root"], "--certificate", public["certificate"],
                                    "--module-id", module_id, "--algorithms", "Ed25519"])
            run(name + "-sign", [*prefix, "sign", source, "--policy", policy, "--key", ca["key"],
                                 "--certificate", ca["certificate"], "--crl", ca["crl"], "--module-id", module_id,
                                 "--module-version", "1", "--algorithm", "Ed25519", "--not-before", stamp(-90),
                                 "--not-after", stamp(3600), "--output", result])
            return result, policy
        signed, policy = sign("release", "wros.sdk.memory.release", unsigned)
        site = dict(release_sha256=canonical(row), trust=dict(verifier=str(args.cosign.resolve()),
                    verifier_sha256=sha(args.cosign), statement=str(signed), statement_sha256=sha(signed), policy=str(policy)))
        config = out / "operator.json"
        install = [sys.executable, "-B", SDK / "install/bootstrap.py", "install", "--commit", args.commit,
                   "--platform", "unitree", "--language", "go", "--local-repository", SDK, "--site-profile", config]
        config.write_text(json.dumps(dict(site, release_sha256="0"*64)))
        run("deny-wrong-row", [*install, "--prefix", out / "denied"], False)
        config.write_text(json.dumps(dict(site, trust=dict(site["trust"], statement_sha256="0"*64))))
        run("deny-wrong-statement", [*install, "--prefix", out / "denied"], False)
        config.write_text(json.dumps(site))
        installed = json.loads(run("install-signed", [*install, "--prefix", out / "site"]).read_bytes())
        root = Path(installed["directory"])
        body = out / "body.wasm"
        run("signed-site-compile", [root / "bin/wrgo", root / "examples/shared/common/go/controller.go",
                                   "-o", body, "--build-receipt"])
        if json.loads(Path(str(body)+".wros-go.json").read_bytes())["site_release_sha256"] != canonical(row):
            raise ValueError("guest receipt does not bind the signed release")
        guest_id = "wros.test.go.controller"
        signed_guest, guest_policy = sign("guest", guest_id, body)
        run("guest-cosign-verify", [args.cosign, "wasm", "secure", "verify", signed_guest, "--policy", guest_policy])
        for engine in ("int", "aot"):
            argv = [args.vm, "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path",
                    "disable", "--secure", "named-module"]
            run(engine + "-signed", [*argv, signed_guest, guest_policy, guest_id, "--run", signed_guest])
            run(engine + "-unsigned-denied", [*argv, body, guest_policy, guest_id, "--run", body], False)
    (out / "results.json").write_text(json.dumps(dict(commit=args.commit, release_sha256=canonical(row),
        vm_sha256=sha(args.vm), guest_sha256=sha(signed_guest), cases=cases), indent=2) + "\n")


if __name__ == "__main__":
    main()
