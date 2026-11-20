"""@file upstream_c_libraries.py
@brief Run pinned upstream C library tests on native and with the installed SDK.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time

PINS = {"rcutils": "fcc37e51b4d6017dfbebee161d92c7c2fc3d9596", "cjson": "c859b25da02955fef659d658b8f324b5cde87be3",
        "zlib": "da607da739fa6047df13e66a2af6b8bec7c2a498"}
CJSON_CASES = (
    "parse_examples", "parse_number", "parse_hex4", "parse_string", "parse_array", "parse_object",
    "parse_value", "print_string", "print_number", "print_array", "print_object",
    "print_value", "parse_with_opts", "compare_tests", "cjson_add", "minify_tests", "misc_tests",
)
CJSON_UNITY = ("UNITY_EXCLUDE_SETJMP_H=1", "UNITY_OUTPUT_CHAR=wros_unity_no_output",
               "UNITY_OUTPUT_CHAR_HEADER_DECLARATION=wros_unity_no_output(int)")
ZLIB_CORE = "adler32 crc32 deflate inffast inflate inftrees trees zutil".split()


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "sources", "site", "vm", "output"):
        parser.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    parser.add_argument("--commit", required=True)
    choices = ["rcutils-uint8-array", "zlib-example", *("cjson-" + name for name in CJSON_CASES)]
    parser.add_argument("--case", action="append", choices=choices, help="repeat to replay selected upstream tests")
    a = parser.parse_args()
    selected = set(a.case or choices)
    sys.path[:0] = [str(a.sdk / "tests"), str(a.sdk / "install")]
    from separate_compilation import cgroup_record
    from bootstrap import Source, install
    from guest_profile import Profile
    from imports import inspect
    cgroup = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    a.output.mkdir(mode=0o700)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("UWVM_", "WROS_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", LC_ALL="C", TMPDIR=str(a.output), PYTHONDONTWRITEBYTECODE="1")
    git = "/usr/bin/git"
    report = dict(complete=False, sdk_commit=a.commit, vm_sha256=sha(a.vm),
                  started_at=datetime.now(timezone.utc).isoformat(), runner_sha256=sha(Path(__file__)),
                  cgroup=cgroup, sources={}, cases={})

    def save():
        temp = a.output / "results.part"
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(a.output / "results.json")

    def run(output, step, argv, timeout=180, cwd=None):
        begin = time.monotonic_ns()
        result = subprocess.run(list(map(str, argv)), env=env, cwd=cwd or output,
                                capture_output=True, timeout=timeout)
        (output / (step + ".log")).write_bytes(result.stdout + result.stderr)
        case = report["cases"][output.name]
        case["steps"][step] = dict(exit=result.returncode, elapsed_ns=time.monotonic_ns() - begin,
                                   stdout_bytes=len(result.stdout), stderr_bytes=len(result.stderr))
        save()
        return result

    selected_libraries = {case.split("-", 1)[0] for case in selected}
    for library, expected in PINS.items():
        if library not in selected_libraries:
            continue
        source = a.sources / library
        actual = subprocess.check_output([git, "-C", source, "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output([git, "-C", source, "status", "--porcelain"])
        if actual != expected or dirty:
            raise ValueError("unexpected source tree: " + library)
        report["sources"][library] = {"commit": actual}
    save()
    installation = install(Source(a.commit, a.sdk), "unitree", "c", a.output / "sdk", [], site_profile=a.site)
    sdk = Path(installation["directory"])
    (a.output / "install.json").write_text(json.dumps(installation, indent=2) + "\n")

    wrc = [sdk / "bin/wrc", "-O3", "-g", "--eh", "--reactor", "--export", "_start", "--build-receipt"]
    native = ["/usr/bin/cc", "-O3", "-g"]
    objdump = Path(json.loads(a.site.read_bytes())["toolchain"]) / "bin/llvm-objdump"
    runtime = [a.vm, *Profile(32, "3.0", False, True, "eh").uwvm_feature_flags(),
               "--wasm-set-main-module-name", "main", "--runtime-compile-threads", "0",
               "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
               "--debug-fault-action", "exit"]
    clock_signatures = {"clock_time_get": ["i32", "i64", "i32"], "clock_res_get": ["i32", "i32"]}
    clock_resources = {"clock_time_get": ("monotonic-clock", "realtime-clock"),
                       "clock_res_get": ("monotonic-resolution", "realtime-resolution")}
    all_passed = True

    def execute(output, native_command, guest_command, native_cwd=None):
        nonlocal all_passed
        case = report["cases"][output.name]
        native_test = output / "native"
        if run(output, "native-build", [*native, *native_command, "-o", native_test]).returncode:
            case["outcome"] = "native-build-error"
        elif run(output, "native-run", [native_test], cwd=native_cwd).returncode:
            case["outcome"] = "native-failure"
        elif run(output, "wrc", [*wrc, *guest_command, "-o", output / "guest.wasm"]).returncode:
            case["outcome"] = "guest-build-error"
        else:
            guest = output / "guest.wasm"
            data = guest.read_bytes()
            receipt = json.loads(guest.with_suffix(".wasm.wros-build.json").read_bytes())
            case.update(wasm_sha256=sha(guest), imports=inspect(data))
            clocks = set()
            for imported in case["imports"]:
                name = imported["name"]
                if (imported["module"] != "wasi_snapshot_preview1" or imported["kind"] != 0
                        or name not in clock_signatures or imported["params"] != clock_signatures[name]
                        or imported["results"] != ["i32"]):
                    break
                clocks.add(name)
            else:
                permissions = []
                if clocks:
                    permissions = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main"]
                    for name in sorted(clocks):
                        permissions += ["--wasip1-single-interface", "main", name, "allow"]
                        for grant in clock_resources[name]:
                            permissions += ["--wasip1-single-grant", "main", grant]
            if (len(clocks) != len(case["imports"]) or receipt["mode"] != "strict"
                    or case["wasm_sha256"] != receipt["artifact_sha256"] or receipt.get("vm_sha256") != report["vm_sha256"]):
                case["outcome"] = "guest-policy-error"
            else:
                decoded = run(output, "wasm-disassembly", [objdump, "-d", guest])
                case["tag_ops"] = {
                    name: decoded.stdout.count(("memtag." + name).encode())
                    for name in ("claim", "reserve", "activate", "release")
                }
                codes = [run(output, engine, [*runtime, "--runtime-" + engine, *permissions, "--run", guest]).returncode
                         for engine in ("int", "aot")]
                tag_ops = case["tag_ops"]
                if decoded.returncode or not (tag_ops["claim"] + tag_ops["reserve"]) or not tag_ops["release"]:
                    case["outcome"] = "guest-tag-evidence-error"
                else:
                    case["outcome"] = "passed" if not any(codes) else "guest-runtime-failure"
        all_passed = all_passed and case["outcome"] == "passed"
        print(output.name, case["outcome"], flush=True)
        save()

    if "rcutils-uint8-array" in selected:
        root = a.sources / "rcutils"
        original = root / "test/test_uint8_array.cpp"
        output = a.output / "rcutils-uint8-array"
        output.mkdir()
        gtest = output / "gtest"
        gtest.mkdir()
        (gtest / "gtest.h").write_text('''#include <string.h>
#define TEST(group, name) void group##_##name()
#define EXPECT_EQ(left, right) do { if (!((left) == (right))) __builtin_trap(); } while (0)
#define ASSERT_EQ(left, right) EXPECT_EQ(left, right)
#define EXPECT_FALSE(value) do { if (value) __builtin_trap(); } while (0)
''')
        wrapper = output / "entry.cc"
        wrapper.write_text(f'''
#include "{original}"
extern "C" void run_upstream_cases(void) {{
    test_uint8_array_default_initialization();
    test_uint8_array_resize();
}}
#ifdef __wasm__
extern "C" void _start(void) {{ run_upstream_cases(); }}
extern "C" void __assert_fail(const char *, const char *, int, const char *) {{
    __builtin_trap();
}}
#else
int main(void) {{ run_upstream_cases(); return 0; }}
#endif
''')
        sources = [root / "src" / (name + ".c") for name in
                   ("uint8_array", "allocator", "error_handling", "snprintf", "strdup")]
        switches = ["-I", output, "-I", root / "include"]
        report["cases"][output.name] = dict(library="rcutils", upstream_file="test/test_uint8_array.cpp",
             upstream_sha256=sha(original), upstream_cases=2,
             configuration="Upstream rcutils stderr diagnostics off, freestanding assertion adapter", steps={})
        execute(output, [*switches, "-DRCUTILS_REPORT_ERROR_HANDLING_ERRORS=0", wrapper, *sources],
                [*switches, "-D", "RCUTILS_REPORT_ERROR_HANDLING_ERRORS=0", wrapper, *sources])

    suite = a.sources / "cjson/tests"
    unity = suite / "unity/src/unity.c"
    for name in CJSON_CASES:
        if "cjson-" + name not in selected:
            continue
        original = suite / (name + ".c")
        count = len(re.findall(r"\bRUN_TEST\s*\(", original.read_text()))
        # The pinned upstream print-number suite deliberately ignores its NaN test.
        ignored = 1 if name == "print_number" else 0
        if not count:
            raise ValueError("expected upstream Unity cases in " + name)
        output = a.output / ("cjson-" + name)
        output.mkdir()
        fixtures = {}
        fixture_reader = ""
        if name == "parse_examples":
            branches = []
            for fixture in sorted((suite / "inputs").iterdir()):
                if not re.fullmatch(r"test[0-9]+(?:\.expected)?", fixture.name) or not fixture.is_file():
                    raise ValueError("unexpected cJSON fixture " + str(fixture))
                data = fixture.read_bytes()
                if not data or len(data) > 64 * 1024:
                    raise ValueError("cJSON fixture size outside the replay bounds")
                fixtures[fixture.name] = hashlib.sha256(data).hexdigest()
                literal = ", ".join(f"0x{byte:02x}" for byte in data)
                branches.append(f"""    if (strcmp(name, "inputs/{fixture.name}") == 0) {{
        static const unsigned char bytes[] = {{{literal}, 0}};
        char *copy = (char *)malloc(sizeof(bytes));
        if (copy != NULL) memcpy(copy, bytes, sizeof(bytes));
        return copy;
    }}""")
            readers = "\n".join(branches)
            fixture_reader = f"""
#define read_file upstream_unused_read_file
#include "{suite / 'common.h'}"
#undef read_file
static char *read_file(const char *name) {{
{readers}
    return NULL;
}}
"""
        wrapper = output / "entry.c"
        wrapper.write_text(f'''
{fixture_reader}
#define main wros_cjson_original_entry
#include "{original}"
#undef main
void wros_unity_no_output(int c) {{ (void)c; }}
void _start(void) {{
    if (wros_cjson_original_entry() != 0 ||
        Unity.NumberOfTests != {count} || Unity.TestFailures != 0 || Unity.TestIgnores != {ignored})
        __builtin_trap();
}}
''')
        report["cases"][output.name] = dict(library="cjson", upstream_file=original.name,
             upstream_sha256=sha(original), expected_unity_cases=count, expected_upstream_ignores=ignored,
             fixture_sha256=fixtures, steps={})
        defines = [arg for flag in CJSON_UNITY for arg in ("-D", flag)]
        execute(output, [original, unity, "-lm"], [*defines, wrapper, unity], native_cwd=suite)

    if "zlib-example" in selected:
        root = a.sources / "zlib"
        original = root / "test/example.c"
        output = a.output / "zlib-example"
        output.mkdir()
        wrapper = output / "entry.c"
        wrapper.write_text(f'''
#include <stdlib.h>
#include <stdio.h>
static int no_printf(const char *format, ...) {{ (void)format; return 0; }}
static int no_fprintf(FILE *stream, const char *format, ...) {{
    (void)stream; (void)format; return 0;
}}
#define printf no_printf
#define fprintf no_fprintf
#define exit(code) __builtin_trap()
#define main wros_zlib_original_entry
#include "{original}"
#undef main
void _start(void) {{
    if (wros_zlib_original_entry(0, NULL) != 0) __builtin_trap();
}}
''')
        sources = [root / (name + ".c") for name in ZLIB_CORE]
        report["cases"][output.name] = dict(library="zlib", upstream_file="test/example.c",
             upstream_sha256=sha(original), configuration="Z_SOLO", steps={})
        execute(output, ["-DZ_SOLO", "-I", root, original, *sources],
                ["-D", "Z_SOLO", "-I", root, wrapper, *sources])
    report["complete"] = True
    report["all_passed"] = all_passed
    save()
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
