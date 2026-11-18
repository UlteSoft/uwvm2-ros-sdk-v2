"""Run the registered C, C++ or embedded Lua managed-memory tests before emitting an unsigned local WSEA release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def git(*args):
    return subprocess.check_output(["git", "-C", ROOT, *args], text=True).strip()


def verify_checkout(commit, language):
    """Bind executed helpers and inputs to Git blobs even with skip-worktree entries."""
    scopes = ("bin", "tests", "install", "include", "share/abi", "share/qualification", "tools/wasm/memtag")
    if language == "lua":
        scopes += ("language/lua", "third-parties/lua", "examples/lua")
    entries = subprocess.check_output(["git", "-C", ROOT, "ls-tree", "-r", "-z", commit, "--", *scopes])
    tracked = set()
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        meta, encoded = entry.split(b"\t", 1)
        mode, kind, object_id = meta.split()
        relative = Path(encoded.decode())
        path = ROOT / relative
        if mode not in (b"100644", b"100755") or kind != b"blob" or path.is_symlink() or not path.is_file():
            raise ValueError("unexpected source entry " + str(relative))
        data = path.read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        if hashlib.sha1(blob).hexdigest().encode() != object_id:
            raise ValueError("SDK source differs from approved commit: " + str(relative))
        tracked.add(relative)
    # Prevent an ignored helper or cached bytecode from shadowing a reviewed Python module.
    for scope in scopes:
        for path in (ROOT / scope).rglob("*"):
            relative = path.relative_to(ROOT)
            if (path.suffix in (".py", ".pyc", ".so") or path.is_symlink()) and relative not in tracked:
                raise ValueError("untracked qualification input " + str(relative))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "runtime", "sysroots", "output"):
        p.add_argument("--" + key, type=lambda s: Path(s).resolve(), required=True)
    p.add_argument("--sdk-commit", required=True, help="independently approved full Git commit")
    for key in ("producer", "vm", "sysroots"):
        p.add_argument("--approved-" + key + "-sha256", required=True)
    p.add_argument("--language", choices=("c", "cpp", "lua"), default="c")
    p.add_argument("--target", choices=("wasm32", "wasm64"), required=True)
    p.add_argument("-O", choices=("2", "3"), default="2")
    p.add_argument("-g", action="store_true")
    p.add_argument("--eh", action="store_true", help="also exercise exact owner retirement across native Wasm exceptions")
    a = p.parse_args()
    if a.language == "lua" and (a.O != "3" or not a.g or not a.eh):
        p.error("the embedded Lua interpreter uses -O3 -g and the EH sysroot")
    if not a.output.is_relative_to(ROOT / ".tmp"):
        p.error("choose a fresh directory under the SDK .tmp")
    if not re.fullmatch(r"[0-9a-f]{40}", a.sdk_commit) or git("rev-parse", "HEAD") != a.sdk_commit:
        p.error("checkout differs from the approved SDK commit")
    # All qualification, packaging and compiler inputs must be from the checked
    # out revision. Ignored work products live under .tmp and are never imported.
    if git("status", "--porcelain", "--untracked-files=normal"):
        p.error("qualification requires a clean SDK checkout")
    verify_checkout(a.sdk_commit, a.language)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / "install"))
    import local_release
    import qualification
    from guest_profile import Profile

    vm_digest = qualification.digest(a.runtime)
    names = ("clang", "wasm-ld", "llc", "llvm-objdump", "llvm-ar", "FileCheck")
    binaries = {name: qualification.digest(a.toolchain / "bin" / name) for name in names}
    if qualification.canonical(binaries) != a.approved_producer_sha256 or vm_digest != a.approved_vm_sha256:
        p.error("qualification inputs differ from the operator-approved source build")
    lock = ROOT / "tools/wasm/memtag/source-lock.json"
    sources = json.loads(lock.read_text())
    if qualification.digest(a.sysroots) != a.approved_sysroots_sha256:
        p.error("sysroot manifest differs from the operator-approved source build")
    receipt = json.loads(a.sysroots.read_text())
    if (receipt.get("sources") != sources["sources"] or
            receipt.get("runtime_diagnostics") != sources["runtime_diagnostics"] or
            receipt.get("producer_allocation_policy") != sources["producer"]["allocation_policy"] or
            receipt.get("compiler_sha256") != binaries["clang"]):
        p.error("sysroot sources or compiler differ from this SDK release")
    # Threaded TLS qualification requires a separate concurrent lifecycle suite.
    bits = int(a.target[4:])
    profile = Profile(bits, mte=True, exceptions="eh" if a.eh else "noeh")
    measured = qualification.measure_inputs(a.language, a, profile)
    a.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = {}
    base = ["--toolchain", a.toolchain, "--runtime", a.runtime]
    settings = ["-O" + a.O, "--debug" if a.g else "--no-debug"]
    exception = ["--eh"] if a.eh else []
    tests = [
        ("stack", "memtag_stack_generations.py", [*base, "--work", a.output / "stack"]),
        ("global", "memtag_global_pointer_origins.py", [*base, *settings, "--work", a.output / "global"]),
        ("aggregate", "memtag_aggregate_pointers.py", ["--llc", a.toolchain / "bin/llc",
            "--linker", a.toolchain / "bin/wasm-ld", "--runtime", a.runtime, "--output", a.output / "aggregate"]),
        ("heap", "memtag_heap_neighbors.py", [*base, *settings, "--candidate-mte", "--address-bits", str(bits),
                                              "--sysroots", a.sysroots, *exception, "--output", a.output / "heap"]),
        ("libc", "memtag_libc_scratch.py", [*base, *exception, "--address-bits", str(bits), "--sysroots", a.sysroots,
                                            "--output", a.output / "libc"]),
    ]
    if a.language == "lua":
        tests.append(("lua", "lua_interpreter.py", [*base, "--sysroots", a.sysroots, "--candidate-mte",
                                                   "--address-bits", str(bits), "--output", a.output / "lua"]))
    for label, script, arguments in tests:
        proc = subprocess.run([sys.executable, "-I", "-B", "-c",
                               "import runpy,sys; p=sys.argv.pop(1); sys.path.insert(0,p);"
                               "s=sys.argv.pop(1); sys.argv[0]=s; runpy.run_path(s,run_name='__main__')",
                               str(ROOT / "tests"), str(ROOT / "tests" / script), *arguments],
                              cwd=ROOT, check=False, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(a.output)}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        (a.output / (label + ".log")).write_bytes(proc.stdout)
        proc.check_returncode()
        log = a.output / label / "results.json"
        evidence = json.loads(log.read_text())
        cases = evidence.get("cases")
        if evidence.get("complete") is not True or not cases or any(
                (step.get("code", step.get("exit")) == 0) != step.get("expected_success", True) for step in cases):
            raise ValueError("incomplete " + label + " execution evidence")
        results[label] = qualification.digest(log)
    if (qualification.measure_inputs(a.language, a, profile) != measured or qualification.digest(a.runtime) != vm_digest or
            qualification.digest(a.sysroots) != a.approved_sysroots_sha256 or
            any(qualification.digest(a.toolchain / "bin" / name) != before for name, before in binaries.items())):
        raise ValueError("qualification inputs changed")
    verify_checkout(a.sdk_commit, a.language)
    if a.language == "cpp":
        heap = json.loads((a.output / "heap/results.json").read_text())
        names = {item["name"] for item in heap["cases"] if item["exit"] == 0}
        stages = ("compile", "disassemble", "int", "aot", "int-runtime-off", "aot-runtime-off")
        if not all(f"libcxx-{bits}-{stage}" in names for stage in stages):
            raise ValueError("missing C++ allocation execution evidence")
    language_proof = {"c": "libc", "cpp": "heap", "lua": "lua"}[a.language]
    row = dict(language=a.language, profile=profile.to_dict(), settings={"optimization": a.O, "debug": a.g},
               inputs=measured, vm_sha256=vm_digest, sdk_commit=a.sdk_commit,
               source_lock_sha256=qualification.digest(lock), producer_programs_sha256=qualification.canonical(binaries),
               sysroots_manifest_sha256=a.approved_sysroots_sha256,
               evidence={"compiler-stack": results["stack"], "global-layout": results["global"],
                         "aggregate-pointers": results["aggregate"], "heap": results["heap"],
                         "language": results[language_proof], "vm-int": results["heap"], "vm-aot": results["heap"]})
    if a.eh:
        log = json.loads((a.output / "heap/results.json").read_text())
        names = {case.get("name") for case in log["cases"] if case.get("exit") == 0}
        expected = {"unwind-" + str(bits) + "-" + suffix for suffix in ("compile", "int", "int-off", "aot", "aot-off")}
        if not expected.issubset(names):
            raise ValueError("missing real C++ unwind and destructor execution evidence")
        row["evidence"]["exception-unwind"] = results["heap"]
    if not qualification.complete_release(row):
        raise ValueError("invalid resulting qualification profile")
    (a.output / "unsigned.wasm").write_bytes(local_release.encode([row]))
    (a.output / "release.json").write_text(json.dumps(row, indent=2) + "\n")


if __name__ == "__main__":
    main()
