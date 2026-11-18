"""Execute numerical test bodies from the pinned ROS source inventory.

The native oracle uses the real GoogleTest included in the ROS source snapshot.
A second native build measures each observed assertion count and predicate trace. A
WASI-free guest must reproduce both for each case on each selected VM engine.
A digest-pinned change to one upstream test is recorded separately. Archive and
closure identity, unselected units and failed steps are retained.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

SDK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "install"))
sys.path.insert(0, str(SDK / "tests"))
from imports import inspect
from guest_profile import Profile
from separate_compilation import cgroup_record

UNITS = {
    "angles": ("test/utest.cpp",),
    "base_local_planner": ("test/line_iterator_test.cpp", "test/velocity_iterator_test.cpp"),
    "rcpputils": ("test/test_accumulator.cpp", "test/test_clamp.cpp", "test/test_pointer_traits.cpp"),
    "nav_core2": ("test/bounds_test.cpp",),
}
GTEST = ("15d437d2af77d057aa4eabdb", "googletest-iron/googletest")
SUPPORT = Path(__file__).with_name("upstream_cpp_support")
TEST = re.compile(r"^\s*TEST\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", re.M)
INCLUDE = re.compile(r'^\s*#\s*include\s*["<]([^">]+)[">]', re.M)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, obj):
    temp = path.with_suffix(".writing")
    temp.write_text(json.dumps(obj, indent=2) + "\n")
    temp.replace(path)


class SourceArchive:
    def __init__(self, corpus, instance):
        self.source_id = instance["source_id"]
        manifest = PurePosixPath(instance["manifest"])
        if not re.fullmatch(r"[a-f0-9]{24}", self.source_id) or manifest.is_absolute() or ".." in manifest.parts:
            raise ValueError("invalid corpus snapshot or manifest path")
        self.package = manifest.parent
        paths = [corpus / place / (self.source_id + ".tar.gz")
                 for place in ("archives", "recovery/archives", "supplemental/archives")]
        path = next(p for p in paths if p.exists())
        if sha(path) != instance["archive_sha256"]:
            raise ValueError("snapshot digest mismatch " + self.source_id)
        self.tar = tarfile.open(path, "r:gz")
        self.files = {}
        for member in self.tar:
            name = PurePosixPath(member.name)
            if not member.isfile() or not name.is_relative_to(self.package):
                continue
            key = name.relative_to(self.package)
            if key.is_absolute() or ".." in key.parts or key in self.files:
                raise ValueError("ambiguous snapshot member " + str(key))
            self.files[key] = member

    def read(self, name):
        member = self.files[PurePosixPath(name)]
        if member.size > 4 * 1024 * 1024:
            raise ValueError("source too large " + member.name)
        with self.tar.extractfile(member) as stream:
            return stream.read()

    def closure(self, unit):
        pending = [PurePosixPath(unit)]
        found = {}
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found[current] = self.read(current)
            for include in INCLUDE.findall(found[current].decode()):
                if include.startswith("/") or ".." in PurePosixPath(include).parts:
                    raise ValueError("external relative include " + include)
                for candidate in (current.parent / include, PurePosixPath("include") / include):
                    if candidate in self.files:
                        pending.append(candidate)
                        break
        return found


def put(root, relative, data):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def command(folder, label, args):
    args = list(map(str, args))
    print(folder.name, label, flush=True)
    record = folder / (label + ".command.json")
    save(record, dict(argv=args))
    try:
        result = subprocess.run(args, cwd=folder, capture_output=True, timeout=180)
    except subprocess.TimeoutExpired as error:
        (folder / (label + ".stdout")).write_bytes(error.stdout or b"")
        (folder / (label + ".stderr")).write_bytes(error.stderr or b"")
        raise ValueError(label + " timed out") from error
    (folder / (label + ".stdout")).write_bytes(result.stdout)
    (folder / (label + ".stderr")).write_bytes(result.stderr)
    save(record, dict(argv=args, exit=result.returncode))
    if result.returncode:
        raise ValueError(label + " failed: " + result.stderr[-1000:].decode(errors="replace"))
    return result.stdout.decode()


def build_gtest(options, index):
    snapshot = next(item for item in index["gtest_vendor"]["instances"] if item["source_id"] == GTEST[0])
    if (str(PurePosixPath(snapshot["manifest"]).parent) != GTEST[1] or snapshot["archive_sha256"] !=
            "5c116c41c774090021dbe985b251afe5a6be9050023e3c086a7b1bf432ee284c"):
        raise ValueError("unexpected GoogleTest package location")
    archive = SourceArchive(options.corpus, snapshot)
    folder = options.output / "native-googletest"
    folder.mkdir()
    try:
        pins = {}
        for name in archive.files:
            if name.parts[0] in ("src", "include") and name.suffix in (".cc", ".h"):
                data = archive.read(name)
                put(folder, name, data)
                pins[str(archive.package / name)] = hashlib.sha256(data).hexdigest()
    finally:
        archive.tar.close()
    save(folder / "pins.json", dict(instance=snapshot, files=pins))
    command(folder, "compile", [options.native_cxx, "-std=c++17", "-O3", "-g", "-pthread",
                                "-include", "cstdint", "-Iinclude", "-I.", "-c", "src/gtest-all.cc", "-o", "gtest.o"])
    return folder


def case_run(folder, unit, cases, validation=None):
    source = ['#include "gtest/gtest.h"', '#define main wros_upstream_original_main',
              '#include "' + unit + '"', '#undef main']
    for suite, name in cases:
        source.append('extern "C" void wros_test_' + suite + "_" + name + '();')
    source += ['#if !defined(__wasm__)', '#include <cstdio>', '#endif', 'int wros_run_all(){']
    for suite, name in cases:
        key = suite + "." + name
        source += ["wros_test::count=0; wros_test::trace=14695981039346656037ull;",
                   f"wros_test_{suite}_{name}();"]
        if validation is None:
            source.append(f'std::printf("{key} %llu %llu\\n",(unsigned long long)wros_test::count,'
                          '(unsigned long long)wros_test::trace);')
        else:
            count, trace = validation[key]
            source.append(f'if(wros_test::count!={count}ull || wros_test::trace!={trace}ull) __builtin_trap();')
    source += ["return 0;}", '#if defined(__wasm__)', 'extern "C" void _start(){wros_run_all();}',
               '#else', 'int main(){return wros_run_all();}', '#endif']
    path = folder / ("native-trace.cpp" if validation is None else "guest.cpp")
    path.write_text("\n".join(source) + "\n")
    return path


def run_case(options, googletest, result, folder, unit, files):
    cases = TEST.findall(files[PurePosixPath(unit)].decode())
    names = [a + "." + b for a, b in cases]
    if not cases or len(set(names)) != len(names):
        raise ValueError("unrecognised or nonunique test bodies")
    result["tests"] = names
    for relative, data in files.items():
        if (str(relative) == "test/velocity_iterator_test.cpp" and hashlib.sha256(data).hexdigest() ==
                "bd5d130ea0a5f57941d794d7298e93558fecdfcccc0646aa83409b152eb97d16"):
            # The original test produces four values but compares five. Initialize
            # the test-owned unused slot; keep the fifth EXPECT_FLOAT_EQ and all
            # algorithm inputs, outputs and source headers unchanged.
            marker = b"TEST(VelocityIteratorTest, test_cranky)"
            before, match, after = data.partition(marker)
            if not match or after.count(b"double result[5];") != 1:
                raise ValueError("unexpected upstream scratch declaration")
            data = before + match + after.replace(b"double result[5];", b"double result[5]{};")
            result["test_only_adaptation"] = dict(
                reason="Original reads an uninitialized fifth slot after producing four results",
                raw_qualification="not qualified; indeterminate upstream comparison",
                sha256=hashlib.sha256(data).hexdigest(), assertions_removed=0)
        put(folder, relative, data)
    common = [options.native_cxx, "-std=c++17", "-O3", "-g", "-UNDEBUG", "-Iinclude"]
    runner = folder / "oracle.cpp"
    runner.write_text('#include <gtest/gtest.h>\n#define main wros_original_main\n#include "' +
                      unit + '"\n#undef main\nint main(int argc, char **argv){'
                      'testing::InitGoogleTest(&argc,argv); return RUN_ALL_TESTS();}\n')
    command(folder, "oracle-compile", [*common, "-pthread", "-I" + str(googletest / "include"),
                                        runner, googletest / "gtest.o", "-o", "oracle"])
    command(folder, "oracle-run", [folder / "oracle", "--gtest_output=xml:oracle.xml"])
    rows = ET.parse(folder / "oracle.xml").findall(".//testcase")
    actual = [c.get("classname") + "." + c.get("name") for c in rows]
    if sorted(actual) != sorted(names) or any(c.get("status") != "run" or c.find("failure") is not None for c in rows):
        raise ValueError("native GoogleTest did not run every recorded test")
    result["native_googletest"] = True
    native_src = case_run(folder, unit, cases)
    command(folder, "native-trace-compile", [*common, "-I" + str(SUPPORT), native_src, "-o", "native-trace"])
    observed = {}
    for line in command(folder, "native-trace-run", [folder / "native-trace"]).splitlines():
        name, count, trace = line.split()
        observed[name] = [int(count), int(trace)]
    if list(observed) != names or any(count == 0 for count, trace in observed.values()):
        raise ValueError("empty or missing upstream assertion trace")
    result["observed_assertions"] = observed
    guest = case_run(folder, unit, cases, observed)
    module = folder / "tests.wasm"
    compiler = [sys.executable, options.sdk / "bin/wrcc", "--toolchain", options.toolchain,
                "--sysroots", options.sysroots, "--target", "wasm32", "--std", "c++17",
                "-O3", "-g", "--reactor", "--export", "_start", "-I", SUPPORT,
                "-I", folder / "include", "--build-receipt"]
    if options.legacy_mte:
        compiler.append("--legacy-mte")
    command(folder, "wrcc", [*compiler, guest, "-o", module])
    if not options.legacy_mte:
        receipt = Path(str(module) + ".wros-build.json")
        command(folder, "strict-artifact", [sys.executable, options.sdk / "install/qualification.py",
                "--artifact", module, "--receipt", receipt, "--vm", options.vm,
                "--approved-receipt-sha256", sha(receipt)])
    result["guest_sha256"] = sha(module)
    result["imports"] = inspect(module.read_bytes())
    if result["imports"]:
        raise ValueError("unexpected guest imports")
    for engine in ("int", "aot"):
        command(folder, "vm-" + engine, [options.vm, *Profile().uwvm_feature_flags(),
                "--debug-fault-action", "exit", "--runtime-" + engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                "--run", module])
        result[engine] = True
    result["passed"] = True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("corpus", "toolchain", "sysroots", "vm", "output"):
        p.add_argument("--" + name, type=lambda x: Path(x).resolve(), required=True)
    p.add_argument("--sdk", type=lambda x: Path(x).resolve(), default=SDK)
    p.add_argument("--installation-receipt", type=Path, help="selection receipt from the SDK installer")
    p.add_argument("--legacy-mte", action="store_true")
    p.add_argument("--native-cxx", type=lambda x: Path(x).resolve(), default=Path("/usr/bin/g++"))
    p.add_argument("--yield-lock", type=Path, help="yield the inherited qualification flock between unique suites")
    options = p.parse_args()
    lock_fd = None
    if options.yield_lock:
        locked = options.yield_lock.stat()
        lock_fd = next((int(f.name) for f in Path("/proc/self/fd").iterdir()
                        if f.exists() and os.path.samestat(f.stat(), locked)), None)
        if lock_fd is None:
            p.error("start the runner under flock on --yield-lock")
    gate = cgroup_record()
    if int(gate["memory_max"]) != 68719476736 or int(gate["swap_max"]) != 0:
        p.error("a 64 GiB, zero-swap qualification cgroup is required")
    if ".tmp" not in options.output.parts:
        p.error("test output must be below a .tmp directory")
    options.output.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(options.output)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    inventory = options.corpus / "linux-five-capability-inventory/packages.json"
    index = {row["name"]: row for row in json.loads(inventory.read_bytes())}
    results = dict(complete=False, scope="listed C++ test translation units", cgroup=gate,
                   inventory_sha256=sha(inventory), vm_sha256=sha(options.vm), sysroots_sha256=sha(options.sysroots),
                   native_compiler_sha256=sha(options.native_cxx), legacy_mte=options.legacy_mte,
                   support_sha256=sha(SUPPORT / "gtest/gtest.h"), runner_sha256=sha(Path(__file__)),
                   compiler_sdk=str(options.sdk), frontend_sha256=sha(options.sdk / "bin/wrcc"),
                   runner_commit=subprocess.check_output(["git", "-C", SDK, "rev-parse", "HEAD"], text=True).strip(),
                   variants=[], unique_suites={})
    if options.installation_receipt is not None:
        selected = json.loads(options.installation_receipt.read_bytes())
        if (Path(selected["directory"]).resolve() != options.sdk or selected["language"] != "cpp" or
                not re.fullmatch(r"[0-9a-f]{40}", selected["commit"])):
            p.error("SDK installation receipt does not identify the selected C++ installation")
        results["compiler_installation"] = dict(commit=selected["commit"], platform=selected["platform"],
                                               variant=selected["variant"], sha256=sha(options.installation_receipt))
    record = options.output / "results.json"
    save(record, results)
    googletest = build_gtest(options, index)
    for name, units in UNITS.items():
        for ref in index[name]["instances"]:
            snapshot = dict(package=name, instance=ref, units={}, unselected_cpp_tests=[])
            results["variants"].append(snapshot)
            archive = SourceArchive(options.corpus, ref)
            try:
                tests = [str(q) for q in archive.files if "test" in q.parts and q.suffix in (".cc", ".cpp", ".cxx")]
                snapshot["unselected_cpp_tests"] = sorted(set(tests) - set(units))
                for unit in units:
                    if PurePosixPath(unit) not in archive.files:
                        snapshot["units"][unit] = dict(status="absent")
                        continue
                    files = archive.closure(unit)
                    pins = {str(q): hashlib.sha256(data).hexdigest() for q, data in sorted(files.items())}
                    key = hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()
                    snapshot["units"][unit] = dict(status="present", closure=key,
                                                  archive_root=str(archive.package), sources=pins)
                    if key not in results["unique_suites"]:
                        if lock_fd is not None and len(results["unique_suites"]) % 4 == 0:
                            fcntl.flock(lock_fd, fcntl.LOCK_UN)
                            time.sleep(0.15)
                            fcntl.flock(lock_fd, fcntl.LOCK_EX)
                        case = results["unique_suites"][key] = dict(package=name, unit=unit, passed=False)
                        folder = options.output / key
                        folder.mkdir()
                        try:
                            run_case(options, googletest, case, folder, unit, files)
                        except (OSError, ValueError, IndexError) as exc:
                            case["error"] = str(exc)
                    save(record, results)
            finally:
                archive.tar.close()
    results["complete"] = True
    results["all_present_suites_passed"] = all(s["passed"] for s in results["unique_suites"].values())
    save(record, results)
    if not results["all_present_suites_passed"]:
        raise SystemExit("one or more present suites did not pass; see results.json")


if __name__ == "__main__":
    main()
