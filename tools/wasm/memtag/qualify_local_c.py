"""Run guest-language managed-memory tests before emitting an unsigned local WSEA release."""
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
    if language == "objectc":
        scopes += ("language/objectc", "third-parties/objectc", "examples/objectc")
    if language == "rs":
        scopes += ("language/rust", "third-parties/rust", "tools/wasm/tag_ir.cpp")
    if language == "tinygo":
        scopes += ("language/tinygo", "tools/wasm/tag_ir.cpp")
    if language == "fortran":
        scopes += ("language/fortran", "third-parties/fortran", "examples/fortran")
    if language == "nim":
        scopes += ("language/nim", "third-parties/nim", "examples/nim")
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
    p.add_argument("--objc-clang", type=lambda s: Path(s).resolve())
    p.add_argument("--objc-runtime", type=lambda s: Path(s).resolve())
    p.add_argument("--approved-objc-inputs-sha256",
                   help="SHA-256 of the canonical Objective-C compiler, runtime receipt and archive digest map")
    p.add_argument("--approved-tinygo-inputs-sha256", help="approved digest of Go, TinyGo and host C++ binary identities")
    p.add_argument("--approved-rust-inputs-sha256", help="approved digest of rustc and host C++ binary identities")
    p.add_argument("--rust-plain-sysroots", type=lambda s: Path(s).resolve(), help="matching Rust opt-out sysroot receipt")
    p.add_argument("--approved-rust-plain-sysroots-sha256")
    p.add_argument("--nim-producer", type=lambda s: Path(s).resolve())
    p.add_argument("--approved-nim-producer-sha256")
    p.add_argument("--approved-flang-sha256", help="approved WebAssembly-only TOOLCHAIN/bin/flang")
    p.add_argument("--approved-marker-sha256", help="approved TOOLCHAIN/bin/wros-flang-mte")
    p.add_argument("--sdk-commit", required=True, help="independently approved full Git commit")
    for key in ("producer", "vm", "sysroots"):
        p.add_argument("--approved-" + key + "-sha256", required=True)
    p.add_argument("--language", choices=("c", "cpp", "lua", "nim", "objectc", "fortran", "tinygo", "rs"), default="c")
    p.add_argument("--target", choices=("wasm32", "wasm64"), required=True)
    p.add_argument("-O", choices=("2", "3"), default="2")
    p.add_argument("-g", action="store_true")
    p.add_argument("--eh", action="store_true", help="also exercise exact owner retirement across native Wasm exceptions")
    a = p.parse_args()
    if a.language == "objectc" and (a.O != "3" or not a.g):
        p.error("the Objective-C language qualification uses -O3 -g")
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

    external = {}
    if a.language == "rs":
        if a.target != "wasm32" or a.O != "3" or not a.g or a.eh:
            p.error("Rust qualification requires wasm32 Core 3.0 single-threaded panic=abort at -O3 -g")
        sys.path.insert(0, str(ROOT / "language/rust"))
        from check_site import inputs as rust_inputs
        external = rust_inputs(a.toolchain)
        if qualification.canonical({k: qualification.digest(v) for k, v in external.items()}) != a.approved_rust_inputs_sha256:
            p.error("Rust frontend or host C++ compiler differs from the approved inputs")
        if not a.rust_plain_sysroots or qualification.digest(a.rust_plain_sysroots) != a.approved_rust_plain_sysroots_sha256:
            p.error("Rust qualification needs an approved plain control sysroot")

    if a.language == "objectc":
        if not a.objc_clang or not a.objc_runtime:
            p.error("Objective-C qualification needs --objc-clang and --objc-runtime")
        external = {"objc_frontend": a.objc_clang, "objc_runtime": a.objc_runtime / "runtime.json",
                    "objc_archive": a.objc_runtime / "libobjc.a"}
        if qualification.canonical({k: qualification.digest(v) for k, v in external.items()}) != a.approved_objc_inputs_sha256:
            p.error("Objective-C frontend or runtime differs from the approved build")
    if a.language == "nim":
        if not a.nim_producer or qualification.digest(a.nim_producer) != a.approved_nim_producer_sha256:
            p.error("Nim requires the independently approved private producer")
        if a.O != "3" or not a.g or not a.eh:
            p.error("Nim qualification currently exercises -O3 -g with the EH sysroot")
        external["producer"] = a.nim_producer
    if a.language == "fortran":
        flang = a.toolchain / "bin/flang"
        marker = a.toolchain / "bin/wros-flang-mte"
        if (a.O != "3" or not a.eh or not flang.is_file() or not marker.is_file() or
                qualification.digest(flang) != a.approved_flang_sha256 or
                qualification.digest(marker) != a.approved_marker_sha256):
            p.error("Fortran qualification requires -O3, EH, the approved Flang and its matching marker")
        external.update(flang=flang, marker=marker)
    if a.language == "tinygo":
        if a.target != "wasm32" or a.O != "3" or not a.g:
            p.error("TinyGo qualification requires single-threaded wasm32 at -O3 -g")
        sys.path.insert(0, str(ROOT / "language/tinygo"))
        from check_site import inputs as tinygo_inputs
        external = tinygo_inputs(a.toolchain)
        if qualification.canonical({k: qualification.digest(v) for k, v in external.items()}) != a.approved_tinygo_inputs_sha256:
            p.error("TinyGo requires the approved Go, TinyGo and host C++ compiler digests")
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
    expected_sources = dict(sources["sources"])
    if receipt.get("producer") == "herbceptions":
        from build_producer import herbceptions_entry
        expected_sources["llvm-23.1.5"] = herbceptions_entry()
    elif a.language == "cpp":
        p.error("a C++ release needs the Wasm Herbceptions compiler and runtime")
    if (receipt.get("sources") != expected_sources or
            receipt.get("runtime_diagnostics") != sources["runtime_diagnostics"] or
            receipt.get("producer_allocation_policy") != sources["producer"]["allocation_policy"] or
            receipt.get("compiler_sha256") != binaries["clang"]):
        p.error("sysroot sources or compiler differ from this SDK release")
    if a.language == "rs":
        plain = json.loads(a.rust_plain_sysroots.read_text())
        for key in ("sources", "runtime_diagnostics", "producer_allocation_policy", "compiler_sha256"):
            if plain.get(key) != receipt[key]:
                p.error("plain Rust control uses another compiler or source closure")
    # Threaded TLS qualification requires a separate concurrent lifecycle suite.
    bits = int(a.target[4:])
    profile = Profile(bits, mte=True, exceptions="eh" if a.eh else "noeh")
    measured = qualification.measure_inputs(a.language, a, profile, external)
    a.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    results = {}
    base = ["--toolchain", a.toolchain, "--runtime", a.runtime]
    settings = ["-O" + a.O, "--debug" if a.g else "--no-debug"]
    exception = ["--eh"] if a.eh else []
    go_flags = []
    if a.language == "tinygo":
        go_flags = ["--goroot", external["go"].parents[1], "--tinygoroot", external["tinygo"].parents[1],
                    "--host-cxx", external["host_cxx"].resolve(strict=True)]
    tests = [
        ("stack", "memtag_stack_generations.py", [*base, "--work", a.output / "stack"]),
        ("global", "memtag_global_pointer_origins.py", [*base, *settings, "--work", a.output / "global"]),
        ("aggregate", "memtag_aggregate_pointers.py", ["--llc", a.toolchain / "bin/llc",
            "--linker", a.toolchain / "bin/wasm-ld", "--runtime", a.runtime, "--output", a.output / "aggregate"]),
        ("heap", "memtag_heap_neighbors.py", [*base, *settings, "--candidate-mte", "--address-bits", str(bits),
                                              "--sysroots", a.sysroots, *exception, *go_flags, "--output", a.output / "heap"]),
        ("libc", "memtag_libc_scratch.py", [*base, *exception, "--address-bits", str(bits), "--sysroots", a.sysroots,
                                            "--output", a.output / "libc"]),
    ]
    if a.language == "cpp":
        tests.append(("herbceptions", "herbceptions/run.py", ["wrcc", "--wrcc", ROOT / "bin/wrcc",
                      "--vm", a.runtime, "--toolchain", a.toolchain, "--sysroots", a.sysroots,
                      "--profile", f"wasm{bits}-{profile.exceptions}", "--feature-flag", "default",
                      "--candidate-mte", "--output", a.output / "herbceptions"]))
    if a.language == "rs":
        tests.append(("rs", "rust_core.py", [*base, "--rustroot", external["rustc"].parents[1],
                                             "--host-cxx", external["host_cxx"], "--sysroots", a.sysroots,
                                             "--plain-sysroots", a.rust_plain_sysroots, "--candidate-mte",
                                             "--output", a.output / "rs"]))
    if a.language == "tinygo":
        tests.append(("tinygo", "tinygo_mte.py", [*base, *go_flags, "--sysroots", a.sysroots, "--profile", profile.exceptions,
                                                 "--candidate-mte", "--output", a.output / "tinygo"]))
    if a.language == "nim":
        tests.append(("nim", "nim_aot.py", [*base, "--sysroots" + str(bits), a.sysroots, "--producer", a.nim_producer,
                                            "--candidate-mte", "--output", a.output / "nim"]))
    if a.language == "lua":
        tests.append(("lua", "lua_interpreter.py", [*base, "--sysroots", a.sysroots, "--candidate-mte",
                                                   "--address-bits", str(bits), "--output", a.output / "lua"]))
    if a.language == "objectc":
        tests.append(("objectc", "objectc.py", [*base, "--target", a.target, "--sysroots", a.sysroots,
                                                "--objc-clang", a.objc_clang, "--objc-runtime", a.objc_runtime,
                                                "--mode", "candidate", "--eh" if a.eh else "--no-eh",
                                                "--output", a.output / "objectc"]))
    if a.language == "fortran":
        language_flags = [*base, "--flang", flang, "--address-width", str(bits), "--sysroots", a.sysroots,
                          "--candidate-mte", *([] if a.g else ["--no-debug"])]
        tests.append(("fortran-compiler", "fortran_compiler.py", ["--flang", flang, "--approved-sha256", a.approved_flang_sha256,
                                                                 "--output", a.output / "fortran-compiler"]))
        tests.append(("fortran-abi", "fortran_aot.py", [*language_flags, "--mte-tool", marker, "--exception-model", "eh",
                                                       "--output", a.output / "fortran-abi"]))
        for name, storage in (("fortran-stack", "stack"), ("fortran-storage", "static-and-heap")):
            tests.append((name, "fortran_stack_neighbors.py", [*language_flags, "--exception-model", "eh", "--storage", storage,
                                                               "--output", a.output / name]))
        tests.append(("fortran-descriptors", "fortran_descriptors.py",
                      [*language_flags, "--output", a.output / "fortran-descriptors"]))
        tests.append(("fortran-intrinsics", "fortran_intrinsics.py",
                      [*language_flags, "--output", a.output / "fortran-intrinsics"]))
        tests.append(("fortran-clocks", "fortran_clocks.py",
                      [*language_flags, "--output", a.output / "fortran-clocks"]))
        tests.append(("fortran-archives", "fortran_archives.py",
                      [*language_flags, "--output", a.output / "fortran-archives"]))
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
                (step.get("code", step.get("exit")) == 0) != step.get("expected_success", step.get("expected", True)) for step in cases):
            raise ValueError("incomplete " + label + " execution evidence")
        results[label] = qualification.digest(log)
    if (qualification.measure_inputs(a.language, a, profile, external) != measured or qualification.digest(a.runtime) != vm_digest or
            qualification.digest(a.sysroots) != a.approved_sysroots_sha256 or
            any(qualification.digest(a.toolchain / "bin" / name) != before for name, before in binaries.items())):
        raise ValueError("qualification inputs changed")
    verify_checkout(a.sdk_commit, a.language)
    if a.language == "rs":
        if qualification.digest(a.rust_plain_sysroots) != a.approved_rust_plain_sysroots_sha256:
            p.error("Rust plain control sysroot changed during qualification")
    if a.language == "cpp":
        heap = json.loads((a.output / "heap/results.json").read_text())
        names = {item["name"] for item in heap["cases"] if item["exit"] == 0}
        stages = ("compile", "disassemble", "int", "aot", "int-runtime-off", "aot-runtime-off")
        if not all(f"libcxx-{bits}-{stage}" in names for stage in stages):
            raise ValueError("missing C++ allocation execution evidence")
    if a.language == "fortran":
        results["fortran"] = qualification.canonical({name: proof for name, proof in results.items() if name.startswith("fortran-")})
    language_proof = {"c": "libc", "cpp": "herbceptions", "lua": "lua", "nim": "nim", "objectc": "objectc", "fortran": "fortran", "tinygo": "tinygo", "rs": "rs"}[a.language]
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
