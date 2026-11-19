"""@brief Qualify a signed standalone Zig SDK with the interpreter and LLVM AOT."""
import argparse
import datetime
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

from separate_compilation import ROOT, cgroup_record, sha
sys.path.insert(0, str(ROOT / "language/zig"))
from driver import build
from release import FORMAT, SETTINGS, local_release, measure, profile_for, qualification


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "sysroots", "no-mte-sysroots", "vm", "vm-source", "cosign", "output", "authority-work"):
        p.add_argument("--" + key, type=lambda value: Path(value).resolve(), required=True)
    p.add_argument("--commit", required=True)
    args = p.parse_args()
    group = cgroup_record()
    os.umask(0o077)
    out = args.output
    out.mkdir(mode=0o700)
    args.authority_work.mkdir(mode=0o700)
    cases = {}
    vm_sha256 = sha(args.vm)
    report = dict(complete=False, cgroup=group, commit=args.commit, vm_sha256=vm_sha256, cases=cases)
    save = lambda: (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, command, failure=None):
        result = subprocess.run(list(map(str, command)), cwd=out, capture_output=True, timeout=240)
        log = out / (name + ".log")
        log.write_bytes(result.stdout + result.stderr)
        cases[name] = dict(exit=result.returncode, log_sha256=sha(log))
        save()
        if failure is None and result.returncode != 0 or failure is not None and (
                result.returncode == 0 or failure not in result.stderr):
            raise RuntimeError(name + " failed: " + log.read_text(errors="replace")[-2100:])
        return result.stdout

    def vm(profile, engine, module, *policy):
        return [args.vm, *profile.uwvm_feature_flags(), "--runtime-" + engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-policy", "fast-compile",
                "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                "--debug-fault-action", "exit", *policy, "--run", module]

    def candidate(profile, label, source):
        scratch = out / (label + "-work")
        scratch.mkdir()
        module = out / (label + ".wasm")
        build(source, module, args.toolchain, [args.sysroots], profile, scratch)
        shutil.rmtree(scratch)
        return module

    common = ROOT / "examples/shared/common/zig/body.zig"
    storage = ROOT / "tests/zig_storage.zig"
    policy = ["--wasm-set-main-module-name", "main", "--ros-scene-create", "robot",
              "--ros-scene-bind", "robot", "main", "--ros-scene-interface", "robot", "abi", "allow"]
    invalid = out / "invalid.zig"
    invalid.write_text('extern "unapproved" fn socket() void;\nexport fn _start() void { socket(); }\n')
    fixture = args.vm_source / "test/0073.ros-tests/support/source/security_wsea/algorithm_matrix.py"
    authority = runpy.run_path(str(fixture))["Fixtures"]
    module_id = "wros.sdk.memory.release"
    now = datetime.datetime.now(datetime.timezone.utc)

    def stamp(seconds):
        return (now + datetime.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for bits in (32, 64):
        tag = "wasm" + str(bits)
        profile = profile_for(bits)
        app = candidate(profile, tag + "-common", common)
        layout = candidate(profile, tag + "-storage", storage)
        for engine in ("int", "aot"):
            run(tag + "-" + engine + "-common", vm(profile, engine, app, *policy))
            run(tag + "-" + engine + "-hidden", vm(profile, engine, app), b"interface is hidden")
            run(tag + "-" + engine + "-storage", vm(profile, engine, layout))
        run(tag + "-missing-site", [sys.executable, "-B", ROOT / "bin/wrzig", common, "-o", out / "refused.wasm"],
            b"needs a signed Zig site")
        run(tag + "-bad-import", [sys.executable, "-B", ROOT / "bin/wrzig", invalid, "-o", out / "refused.wasm",
            "--target", tag, "--no-mte", "--toolchain", args.toolchain, "--sysroots", args.no_mte_sysroots],
            b"unauthorized import or signature")
        assert not (out / "refused.wasm").exists()
        groups = {
            "vm-int": [tag + "-int-common"],
            "vm-aot": [tag + "-aot-common"],
            "storage": [tag + "-int-storage", tag + "-aot-storage"],
            "authority": [tag + "-int-hidden", tag + "-aot-hidden"],
            "admission": [tag + "-missing-site", tag + "-bad-import"],
        }
        inputs = measure(args.toolchain, [args.sysroots], profile)
        row = dict(format=FORMAT, language="zig", profile=profile.to_dict(), settings=SETTINGS,
                   inputs=inputs, vm_sha256=vm_sha256,
                   tests={name: qualification.canonical(dict(cases={c: cases[c] for c in group},
                       source=sha(common), storage=sha(storage), vm=vm_sha256))
                       for name, group in groups.items()})
        protected = args.authority_work / tag
        protected.mkdir()
        unsigned = out / (tag + "-release.wasm")
        unsigned.write_bytes(local_release.encode([row]))
        signed, rules = protected / "signed.wasm", protected / "release.policy"
        prefix = [args.cosign, "wasm", "secure"]
        with tempfile.TemporaryDirectory(dir=protected) as temp:
            ca = authority(Path(temp) / "test").pki("test", family="ED25519")
            root, cert = protected / "root.pem", protected / "certificate.pem"
            shutil.copyfile(ca["root"], root)
            shutil.copyfile(ca["certificate"], cert)
            run(tag + "-policy", [*prefix, "policy-init", "--output", rules, "--state-dir", protected / "state",
                "--trust-root", root, "--certificate", cert, "--module-id", module_id, "--algorithms", "Ed25519"])
            run(tag + "-sign", [*prefix, "sign", unsigned, "--policy", rules, "--key", ca["key"],
                "--certificate", ca["certificate"], "--crl", ca["crl"], "--module-id", module_id, "--module-version", "1",
                "--algorithm", "Ed25519", "--not-before", stamp(-60), "--not-after", stamp(7200), "--output", signed])
        site = dict(toolchain=str(args.toolchain), sysroots=[str(args.sysroots)], release_sha256=qualification.canonical(row),
                    trust=dict(verifier=str(args.cosign), verifier_sha256=sha(args.cosign), statement=str(signed),
                               statement_sha256=sha(signed), policy=str(rules)))
        config = out / (tag + "-site.json")
        config.write_text(json.dumps(site))
        metadata = run(tag + "-install", [sys.executable, "-B", ROOT / "install/bootstrap.py", "install",
                       "--commit", args.commit, "--platform", "unitree", "--language", "zig", "--site-profile", config,
                       "--prefix", out / (tag + "-install"), "--local-repository", ROOT])
        sdk = Path(json.loads(metadata)["directory"])
        report[tag] = dict(sdk=str(sdk), release_sha256=qualification.canonical(row))
        save()
        compiler = [sys.executable, "-B", sdk / "bin/wrzig"]
        module = out / (tag + "-strict.wasm")
        run(tag + "-strict", [*compiler, common, "-o", module, "--build-receipt"])
        receipt_path = Path(str(module) + ".wros-build.json")
        run(tag + "-verify", [*compiler, "verify", "--artifact", module, "--receipt", receipt_path,
                              "--vm", args.vm, "--approved-receipt-sha256", sha(receipt_path)])
        run(tag + "-wrong-width", [*compiler, common, "-o", out / "refused.wasm", "--target",
            "wasm64" if bits == 32 else "wasm32"], b"differs from the signed address width")
        run(tag + "-wrong-receipt", [*compiler, "verify", "--artifact", module, "--receipt", receipt_path,
            "--vm", args.vm, "--approved-receipt-sha256", "0" * 64], b"differs from the operator-approved digest")
        for engine in ("int", "aot"):
            run(tag + "-strict-" + engine, vm(profile, engine, module, *policy))
        plain = out / (tag + "-untagged.wasm")
        run(tag + "-off", [*compiler, common, "--target", tag, "--no-mte", "--toolchain", args.toolchain,
                            "--sysroots", args.no_mte_sysroots, "-o", plain, "--build-receipt"])
        assert json.loads(Path(str(plain) + ".wros-build.json").read_bytes())["mode"] == "off"
        for engine in ("int", "aot"):
            run(tag + "-off-" + engine, vm(profile_for(bits, tagged=False), engine, plain, *policy))
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
