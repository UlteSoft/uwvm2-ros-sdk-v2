"""@file upstream_rust_libraries.py
@brief Replay upstream ArrayVec and ArrayString tests under the SDK no_std profile.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

UPSTREAM = "8267e7e5614569192bd794fea9e88f85ed913eb8"
CASES = (
    "test_capacity_left", "test_extend_from_slice", "test_extend_from_slice_error",
    "test_try_from_slice_error", "test_u16_index", "test_iter", "test_extend",
    "test_drain", "test_drain_range_inclusive", "test_retain", "test_insert",
    "test_into_inner_1", "test_into_inner_3", "test_take", "test_string_from",
    "test_string_parse_from_str", "test_string_from_bytes", "test_string_clone",
    "test_string_push", "test_insert_at_length", "test_drop_in_insert",
    "test_extend_zst", "test_try_from_argument", "allow_max_capacity_arrayvec_type",
    "test_arraystring_const_constructible", "test_arraystring_zero_filled_has_some_sanity_checks",
)
LEGACY_ASSERT_IMPORT = "#[macro_use] extern crate matches;"
ARCH = "x86_64-unknown-linux-gnu"


def sha(path):
    """@brief Identify the actual inputs and build artifact."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module_for_guest(source, work):
    """@brief Preserve the selected upstream function bodies and replace only the test runner."""
    work.mkdir()
    tests = (source / "tests/tests.rs").read_text()
    definitions = {}
    for match in re.finditer(r"(?m)^fn ([a-z0-9_]+)\(\) \{\n", tests):
        if match[1] not in CASES:
            continue
        end = tests.index("\n}\n", match.end())
        if match[1] in definitions:
            raise ValueError("duplicate upstream case " + match[1])
        definitions[match[1]] = tests[match.start():end + 3]
    if set(definitions) != set(CASES):
        raise ValueError("unexpected upstream test declarations")
    module = work / "wros_upstream_tests.rs"
    module.write_text("#![no_std]\nuse arrayvec::{ArrayString, ArrayVec, CapacityError};\n"
                      "use core as std;\nuse core::assert_matches;\n\n"
                      + "\n".join(definitions[name] for name in CASES)
                      + "\npub fn run() {\n"
                      + "".join(f"    {name}();\n" for name in CASES)
                      + "}\n")
    entry = work / "body.rs"
    entry.write_text('''#![no_std]

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    arrayvec_replay::run();
}

#[panic_handler]
fn wros_test_panic(_: &core::panic::PanicInfo<'_>) -> ! {
    core::arch::wasm32::unreachable()
}
''')
    return entry, module


def main():
    """@brief Execute native and installed SDK profiles with distinct evidence for each."""
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "source", "rustroot", "vm", "output"):
        cli.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve(strict=False))
    cli.add_argument("--commit", required=True)
    tool = cli.add_mutually_exclusive_group(required=True)
    tool.add_argument("--site", type=Path)
    tool.add_argument("--plain-sysroots", type=Path)
    cli.add_argument("--toolchain", type=Path)
    cli.add_argument("--xmake", type=Path)
    a = cli.parse_args()
    if a.plain_sysroots and a.toolchain is None:
        cli.error("explicit MTE off requires the matching toolchain and no-EH sysroot")
    if a.xmake and a.site is None:
        cli.error("the Xmake replay requires a signed Rust site")
    sdk_repo, source, out = a.sdk, a.source, a.output
    sys.path[:0] = [str(sdk_repo / "tests"), str(sdk_repo / "install")]
    from separate_compilation import cgroup_record
    from bootstrap import Source, install
    from guest_profile import Profile
    from imports import inspect
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    revision = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    if revision != UPSTREAM or subprocess.check_output(["git", "-C", source, "status", "--porcelain"]):
        raise ValueError("expected a clean exact ArrayVec checkout")
    out.mkdir(mode=0o700)
    compiler = a.rustroot / "bin/rustc"
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("RUST", "WROS_", "UWVM_", "CARGO", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", LC_ALL="C", TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, cgroup=group, source_commit=revision, sdk_commit=a.commit,
                  vm_sha256=sha(a.vm), upstream_test_sha256=sha(source / "tests/tests.rs"),
                  guest_cases=CASES, steps={})
    result = out / "results.json"

    def save():
        result.write_text(json.dumps(report, indent=2) + "\n")

    def run(label, argv, timeout=300, *, cwd=out, environment=env, denial=None):
        print(label, flush=True)
        proc = subprocess.run(list(map(str, argv)), cwd=cwd, env=environment, capture_output=True, timeout=timeout)
        (out / (label + ".log")).write_bytes(proc.stdout + proc.stderr)
        report["steps"][label] = {"exit": proc.returncode}
        save()
        rejected = proc.returncode != 0
        if (denial is None and rejected) or (denial is not None and (not rejected or denial not in proc.stderr)):
            raise RuntimeError(label + " failed")
        return proc.stdout

    native_common = [compiler, "--target", ARCH, "--edition=2018", "-C", "opt-level=3", "-C", "debuginfo=2"]
    lib = out / "libarrayvec.rlib"
    run("native-library", [*native_common, "--crate-name", "arrayvec", "--crate-type", "rlib",
                           source / "src/lib.rs", "-o", lib])
    test_source = (source / "tests/tests.rs").read_text()
    if test_source.count(LEGACY_ASSERT_IMPORT) != 1:
        raise ValueError("unexpected upstream assertion import")
    native_test = out / "native-tests.rs"
    native_test.write_text(test_source.replace(LEGACY_ASSERT_IMPORT, "use std::assert_matches;"))
    native = out / "native-tests"
    run("native-test-build", [*native_common, "--crate-name", "native_tests", "--test", native_test,
                              "--extern", "arrayvec=" + str(lib), "-o", native])
    output = run("native-test", [native, "--test-threads=1"])
    count = re.search(rb"test result: ok\. ([0-9]+) passed; 0 failed", output)
    if not count:
        raise ValueError("native upstream test summary is missing")
    report["native_passed"] = int(count[1])
    installed = install(Source(a.commit, sdk_repo), "unitree", "rs", out / "sdk", [], site_profile=a.site)
    sdk = Path(installed["directory"])
    guest, cases = module_for_guest(source, out / "guest-src")
    library = source / "src/lib.rs"
    wasm = out / "arrayvec.wasm"
    opts = [] if a.site else ["--no-mte", "--rustroot", a.rustroot, "--toolchain", a.toolchain,
                              "--sysroots", a.plain_sysroots, "-O3", "-g"]
    wrrs = [sdk / "bin/wrrs", guest, *opts]
    run("wrrs", [*wrrs, "--library", "arrayvec", library, "--library", "arrayvec_replay", cases,
                 "--build-receipt", "--print-identity", "-o", wasm])
    for label, args, denial in (
        ("reject-reserved-name", ["--library", "core", library], b"reserved Rust crate name"),
        ("reject-duplicate-name", ["--library", "arrayvec", library, "--library", "arrayvec", cases], b"duplicate"),
        ("reject-binary-dependency", ["--library", "arrayvec", lib], b"must be a .rs file"),
    ):
        run(label, [*wrrs, *args, "-o", out / "refused.wasm"], denial=denial)
        if (out / "refused.wasm").exists():
            raise ValueError("rejected dependency left a Wasm artifact")
    profile = Profile(32, "3.0", False, bool(a.site), "noeh")
    receipt = json.loads(wasm.with_suffix(".wasm.wros-build.json").read_bytes())
    if receipt["profile"] != profile.to_dict() or receipt["artifact_sha256"] != sha(wasm):
        raise ValueError("unexpected Rust guest build receipt")
    if a.site and (receipt["mode"] != "strict" or receipt["vm_sha256"] != report["vm_sha256"]):
        raise ValueError("the signed Rust profile must qualify the exact VM")
    if not a.site and receipt["mode"] != "off":
        raise ValueError("explicit MTE off did not select the recorded profile")
    imports = inspect(wasm.read_bytes())
    if imports:
        raise ValueError("the portable upstream ArrayVec cases must use no host imports")
    report.update(wasm_sha256=receipt["artifact_sha256"], profile=receipt["profile"], imports=imports,
                  native_test_source_sha256=sha(native_test), guest_test_source_sha256=sha(cases))
    if a.site:
        objdump = Path(json.loads(a.site.read_bytes())["toolchain"]) / "bin/llvm-objdump"
        disassembly = run("disassembly", [objdump, "-d", wasm])
        report["wasmmte_owner_ops"] = {n: disassembly.count(("memtag." + n).encode())
                                        for n in ("claim", "reserve", "activate", "release")}
        if not report["wasmmte_owner_ops"]["release"] or not report["wasmmte_owner_ops"]["reserve"]:
            raise ValueError("the strict port did not contain managed stack operations")
    tag_policy = ["--runtime-memtag-mode", "sync"] if a.site else ["--runtime-disable-memtag"]
    flags = profile.uwvm_feature_flags()
    if "--wasm-feature-enable-exceptions" in flags:
        flags[flags.index("--wasm-feature-enable-exceptions")] = "--wasm-feature-disable-exceptions"
    for engine in ("int", "aot"):
        run(engine, [a.vm, *flags, *tag_policy, "--runtime-" + engine, "--runtime-compile-threads", "0",
                     "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit", "--run", wasm])
    if a.xmake:
        (guest.parent / "xmake.lua").write_text(f'''set_project("arrayvec-upstream")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("arrayvec")
    set_kind("binary")
    set_language("rs")
    set_ros_platform("unitree")
    set_wros_profile({{eh = false}})
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_rust_library("arrayvec", {json.dumps(str(library), ensure_ascii=False)})
    add_wros_rust_library("arrayvec_replay", "wros_upstream_tests.rs")
    add_files("body.rs")
    add_wros_tests("int", "aot")
target_end()
''')
        xenv = {**env, "XMAKE_GLOBALDIR": str(out / "xmake-global"), "XMAKE_STATS": "false",
                 "UWVM_ROS_SDK_ROOT": str(sdk), "WROS_VM": str(a.vm)}
        for label, args in (
            ("configure-xmake", ["f", "-p", "wasm-wasip1", "-a", "wasm32", "-y"]),
            ("build-xmake", ["build", "-j1"]),
            ("test-xmake", ["test", "-j1"]),
        ):
            run(label, [a.xmake, *args], cwd=guest.parent, environment=xenv)
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
