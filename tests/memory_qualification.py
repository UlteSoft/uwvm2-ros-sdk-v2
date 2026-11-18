"""Exercise public strict admission, explicit opt-outs, and independently approved artifact verification."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from separate_compilation import ROOT, Profile, cgroup_record, sha
import artifacts
import qualification as q


def policy_fixture(work, run):
    """Use an isolated invented trust store and inert test identities, never a release."""
    sdk = work / "policy-fixture"
    tool = sdk / "tc"
    for name in (*q.COMMON, *q.SDK_INPUTS["c"], "tc/bin/wasm-ld", "tc/bin/llvm-ar"):
        path = sdk / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    index = sdk / q.INDEX
    index.parent.mkdir(parents=True)
    compiler = hashlib.sha256(b"inert-test-compiler").hexdigest()
    closure = hashlib.sha256(b"inert-test-sysroot").hexdigest()
    options = SimpleNamespace(mte=True, legacy_mte=False, O="3", g=True, toolchain=tool,
                              sysroots=[sdk / "test-closure"], build_receipt=True)
    target = Profile()
    vm = sdk / "inert-vm-identity"
    vm.write_bytes(b"fixture, never executed")
    def trust(rows):
        index.write_text(json.dumps(dict(format="wros-memory-neighbor-releases", managed_gap_bytes=64, routes=rows)))
    def expected_denial(label, op):
        try:
            op()
        except (ValueError, KeyError):
            run.append(label)
        else:
            raise AssertionError(label + ": should refuse")
    def admit():
        return q.admit("c", options, target, sdk=sdk)
    with patch.object(q, "make_command", return_value=([], dict(compiler_sha256=compiler, closure_sha256=closure))):
        inputs = q.measure_inputs("c", options, target, sdk=sdk)
        row = dict(language="c", profile=target.to_dict(), settings={"optimization":"3","debug":True},
                   inputs=inputs, vm_sha256=sha(vm),
                   evidence={name: hashlib.sha256(("fixture-" + name).encode()).hexdigest() for name in q.PROOFS | {"exception-unwind"}})
        trust([])
        expected_denial("unlisted-candidate", admit)
        incomplete = copy.deepcopy(row)
        del incomplete["evidence"]["vm-aot"]
        trust([incomplete])
        expected_denial("incomplete-evidence", admit)
        trust([row, row])
        expected_denial("ambiguous-release", admit)
        trust([row])
        record = admit()
        assert record["release_sha256"] == q.canonical(row)
        run.append("isolated-reviewed-route")
        (tool / "bin/wasm-ld").write_bytes(b"changed")
        expected_denial("replaced-linker", admit)
        (tool / "bin/wasm-ld").write_bytes(b"tc/bin/wasm-ld")
        (sdk / "bin/wrc").write_bytes(b"changed")
        expected_denial("replaced-frontend", admit)
        (sdk / "bin/wrc").write_bytes(b"bin/wrc")
        options.g = False
        expected_denial("unreviewed-debug-setting", admit)
        options.g = True
        assert not q.valid_proofs(row, threads=True)
        without_unwind = copy.deepcopy(row)
        del without_unwind["evidence"]["exception-unwind"]
        assert not q.complete_release(without_unwind)
        run.append("threaded-release-needs-tls")
        other = copy.deepcopy(row)
        other["inputs"]["sysroot"] = "7"*64
        trust([row, other])
        allowed = q.object_releases(record, sdk)
        assert allowed == {q.canonical(row)}
        run.append("incompatible-object-release-excluded")
        obj = artifacts.MAGIC + b"\x00\x09\x07linking\x02"
        previous = artifacts.seal_object(obj, target.to_dict(), compiler, closure)
        check = lambda data: artifacts.check_object(data,target.to_dict(),compiler,closure,allowed)
        expected_denial("unreviewed-object", lambda:check(previous))
        check(artifacts.seal_object(obj, target.to_dict(), compiler, closure, q.canonical(row)))
        run.append("reviewed-object")
        trust([row])
        guest = sdk / "register.wasm"
        # A valid pure-register () -> i32 function. All section envelopes are real.
        def publish(build_record):
            staged = sdk / "test.stage"
            staged.write_bytes(guest.read_bytes())
            q.finish(build_record, options, staged, guest)
        guest.write_bytes(bytes.fromhex("0061736d010000000105016000017f030201000a0601040041070b"))
        publish(record)
        receipt = Path(str(guest)+".wros-build.json")
        approved = sha(receipt)
        assert q.verify(guest, receipt, vm, approved, sdk)["mode"] == "strict"
        run.append("register-only-module-independent-of-opcode")
        incomplete = copy.deepcopy(row)
        del incomplete["inputs"]["compiler"]
        trust([incomplete])
        publish(dict(record, release_sha256=q.canonical(incomplete)))
        expected_denial("incomplete-inputs-at-deployment", lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))
        trust([row])
        publish(record)
        approved = sha(receipt)
        # Deterministically interleave another writer immediately after our
        # module rename. Our receipt must still describe our private bytes.
        staged = sdk / "racing.stage"
        original = guest.read_bytes()
        changed = original[:-2] + b"\x09\x0b"
        staged.write_bytes(original)
        rename = os.replace
        def interleave(src, dst):
            rename(src, dst)
            if Path(dst) == guest:
                guest.write_bytes(changed)
        with patch.object(q.os, "replace", side_effect=interleave):
            q.finish(record, options, staged, guest)
        assert json.loads(receipt.read_bytes())["artifact_sha256"] == hashlib.sha256(original).hexdigest()
        expected_denial("interleaved-output-replacement", lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))
        guest.write_bytes(original)
        publish(record)
        approved = sha(receipt)
        staged.write_bytes(changed)
        expected_denial("oversized-receipt-preserves-output",
                        lambda: q.finish(record, options, staged, guest, {"large": "x" * q.MAX_RECEIPT_BYTES}))
        assert guest.read_bytes() == original and sha(receipt) == approved

        guest.write_bytes(guest.read_bytes()[:-2] + b"\x08\x0b")
        expected_denial("changed-application", lambda:q.verify(guest, receipt, vm, approved,sdk))
        publish(record)
        expected_denial("receipt-not-reviewed-for-second-application", lambda:q.verify(guest, receipt,vm, approved,sdk))
        q.verify(guest,receipt,vm,sha(receipt),sdk)
        run.append("same-reviewed-producer-new-application")
        vm.write_bytes(b"changed")
        expected_denial("changed-vm", lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))
        vm.write_bytes(b"fixture, never executed")
        guest.write_bytes(previous)
        publish(record)
        expected_denial("relocatable-object-as-final-module", lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))
        guest.write_bytes(artifacts.MAGIC)
        for mode in ("off","legacy"):
            publish(dict(record, mode=mode))
            expected_denial("misrepresented-"+mode, lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))
        publish(record)
        receipt.write_bytes(receipt.read_bytes().replace(b'"mode": "strict"', b'"mode":"strict","mode":"strict"'))
        expected_denial("duplicate-record-field", lambda:q.verify(guest,receipt,vm,sha(receipt),sdk))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain","sysroots","plain-sysroots","runtime","flang","mte-tool","rustroot","goroot","tinygoroot","output"):
        p.add_argument("--"+name, type=lambda value: Path(value).resolve(), required=True)
    a = p.parse_args()
    work = a.output
    if not work.is_relative_to(ROOT / ".tmp"):
        p.error("choose a new SDK .tmp output directory")
    state = {"complete":False, "cgroup":cgroup_record(), "inputs":{}, "checks":[], "commands":[]}
    work.mkdir(parents=True, exist_ok=False)
    common = ["--toolchain",a.toolchain,"--sysroots",a.sysroots]
    env = dict(os.environ, PATH="/usr/bin:/bin", TMPDIR=str(work))
    src = work / "register.c"
    src.write_text("int answer(void) { return 42; }\n")
    def save():
        (work/"results.json").write_text(json.dumps(state, indent=2)+"\n")
    def command(label, argv, diagnostic=None):
        cmd = list(map(str,argv))
        proc = subprocess.run(cmd,cwd=work,env=env,capture_output=True,timeout=150)
        state["commands"].append(dict(label=label, argv=cmd, exit=proc.returncode))
        (work/(label+".stderr")).write_bytes(proc.stderr)
        save()
        if bool(proc.returncode) != bool(diagnostic) or (diagnostic and diagnostic.encode() not in proc.stderr):
            raise RuntimeError(label + ": "+proc.stderr.decode(errors="replace")[-1200:])
        return proc
    policy_fixture(work, state["checks"])
    work.joinpath("go.mod").write_text("module example.local/core\n\ngo 1.24\n")
    fr = work/"test.f90"
    fr.write_text("program t\nend program\n")
    for frontend, inputs in (
        ("wrc",[src]), ("wrcc",[src]), ("wrlua",[src]), ("wrrs",[src.with_suffix(".rs"),"--rustroot",a.rustroot]),
        ("wrf",[fr,"--flang",a.flang,"--mte-tool",a.mte_tool]),
        ("wrtg",[work,"--goroot",a.goroot,"--tinygoroot",a.tinygoroot])):
        if frontend=="wrrs": src.with_suffix(".rs").write_text("// tiny empty crate\n")
        out=work/(frontend+".wasm")
        command(frontend+"-legacy-producer-default-denied",[sys.executable,ROOT/"bin"/frontend,*inputs,*common,"-o",out],
                "reviewed strict-neighbor release")
        assert not out.exists()
    for bits in (32,64):
        for flag, receipt in (("--legacy-mte",a.sysroots),("--no-mte",a.plain_sysroots)):
            name=f"wasm{bits}"+flag
            out=work/(name+".wasm")
            args=[sys.executable,ROOT/"bin/wrc",src,"--toolchain",a.toolchain,"--sysroots",receipt,"--target",f"wasm{bits}",
                  flag,"--build-receipt","--reactor","--export","answer","-O3","-g","-o",out]
            result=command(name+"-compile",args)
            sidecar=Path(str(out)+".wros-build.json")
            report=json.loads(sidecar.read_bytes())
            assert report["artifact_sha256"]==sha(out) and report["mode"]==("legacy" if flag=="--legacy-mte" else "off")
            assert (b"without managed-neighbor qualification" in result.stderr)==(flag=="--legacy-mte")
            command(name+"-denied-as-strict",[sys.executable,ROOT/"install/qualification.py","--artifact",out,"--vm",a.runtime,
                   "--receipt",sidecar,"--approved-receipt-sha256",sha(sidecar)],"does not qualify")
    paths=[Path(__file__), ROOT/"install/qualification.py", ROOT/q.INDEX, a.toolchain/"bin/clang",a.sysroots,a.plain_sysroots,a.runtime]
    state["inputs"]={str(path):sha(path) for path in paths}
    state["complete"]=True
    save()
    print(f"{len(state['checks'])} policy checks, {len(state['commands'])} public CLI commands")


if __name__=="__main__":
    main()
