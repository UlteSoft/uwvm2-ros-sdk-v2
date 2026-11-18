"""Recompile the exact verified upstream test sources against a signed, installed C++ SDK."""
import argparse
import copy
import errno
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess

import upstream_cpp as suite
from upstream_cpp_report import generate, read


def retain(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.copyfile(source, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("previous", "sdk", "installation-receipt", "toolchain", "sysroots", "vm", "output"):
        parser.add_argument("--" + name, type=lambda x: Path(x).resolve(), required=True)
    options = parser.parse_args()
    options.legacy_mte = False
    if ".tmp" not in options.output.parts:
        parser.error("use a fresh project .tmp directory")
    gate = suite.cgroup_record()
    if int(gate["memory_max"]) != 68719476736 or int(gate["swap_max"]) != 0:
        parser.error("a 64 GiB zero-swap cgroup is required")
    previous = read(options.previous)
    review = generate(options.previous)
    if not review["all_present_suites_passed"] or previous["support_sha256"] != suite.sha(suite.SUPPORT / "gtest/gtest.h"):
        parser.error("a complete matching native and guest baseline is required")
    installation = read(options.installation_receipt)
    if (Path(installation["directory"]).resolve() != options.sdk or installation["language"] != "cpp" or
            not re.fullmatch(r"[0-9a-f]{40}", installation["commit"])):
        parser.error("installation receipt does not identify this C++ SDK")
    options.output.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(options.output)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    native = options.previous.parent
    retain(native / "native-googletest/gtest.o", options.output / "native-googletest/gtest.o")
    retain(native / "native-googletest/pins.json", options.output / "native-googletest/pins.json")
    results = dict(complete=False, scope="signed guest replay using independently verified native GoogleTest and trace baselines",
                   native_evidence_sha256=suite.sha(options.previous), cgroup=gate, legacy_mte=False,
                   vm_sha256=suite.sha(options.vm), sysroots_sha256=suite.sha(options.sysroots),
                   compiler_sdk=str(options.sdk), frontend_sha256=suite.sha(options.sdk / "bin/wrcc"),
                   compiler_installation=dict(commit=installation["commit"], platform=installation["platform"],
                                              variant=installation["variant"], sha256=suite.sha(options.installation_receipt)),
                   support_sha256=previous["support_sha256"], inventory_sha256=previous["inventory_sha256"],
                   native_compiler_sha256=previous["native_compiler_sha256"], replay_sha256=suite.sha(Path(__file__)),
                   runner_sha256=suite.sha(Path(suite.__file__)),
                   runner_commit=subprocess.check_output(["git","-C",suite.SDK,"rev-parse","HEAD"], text=True).strip(),
                   variants=previous["variants"], unique_suites={})
    target = options.output / "results.json"
    suite.save(target, results)
    pins = {r["closure"]: r["sources"] for v in previous["variants"] for r in v["units"].values() if r["status"] == "present"}
    for key, old in previous["unique_suites"].items():
        source, folder = native / key, options.output / key
        folder.mkdir()
        # Preserve original compiler commands, stdout, native binaries and XML.
        # The Wasm source and guest artifacts are freshly produced below.
        for name in ("oracle", "oracle.cpp", "oracle.xml", "native-trace", "native-trace.cpp"):
            retain(source / name, folder / name)
        for stage in ("oracle-compile", "oracle-run", "native-trace-compile", "native-trace-run"):
            for suffix in (".command.json", ".stdout", ".stderr"):
                retain(source / (stage + suffix), folder / (stage + suffix))
        for name, upstream in pins[key].items():
            expected = old["test_only_adaptation"]["sha256"] if "test_only_adaptation" in old and name == old["unit"] else upstream
            retain(source / name, folder / name)
            if suite.sha(folder / name) != expected:
                raise ValueError("pinned source changed " + name)
        result = {field: copy.deepcopy(old[field]) for field in ("package", "unit", "tests", "observed_assertions", "native_googletest")}
        if "test_only_adaptation" in old:
            result["test_only_adaptation"] = old["test_only_adaptation"]
        result["passed"] = False
        results["unique_suites"][key] = result
        try:
            cases = suite.TEST.findall((folder / old["unit"]).read_text())
            if [a + "." + b for a, b in cases] != old["tests"]:
                raise ValueError("case inventory changed")
            suite.run_guest(options, result, folder, old["unit"], cases, old["observed_assertions"])
        except (OSError, ValueError) as error:
            result["error"] = str(error)
        suite.save(target, results)
    results["complete"] = True
    results["all_present_suites_passed"] = all(v["passed"] for v in results["unique_suites"].values())
    suite.save(target, results)
    if not results["all_present_suites_passed"]:
        raise SystemExit("strict guest replay failed; see results.json")


if __name__ == "__main__":
    main()
