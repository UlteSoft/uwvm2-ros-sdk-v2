"""@file upstream_libraries.py
@brief Replay original ROS angles and PyPA packaging assertions in the CPython guest.
"""
import argparse
import ast
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile

ANGLES_REVISION = "a96224f9ab3ac51fe8fd981c1e1554528dc4345a"
PACKAGING_REVISION = "f58537628042c7f29780b9d33f31597e7fc9d664"
PACKAGING_SHA = "8f0606147c38fefad972f9653586c3f0e46d8a056d27499e4a5ed952e712d953"
CPYTHON_SHA = "c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73"
STDLIB = (
    "__future__", "_colorize", "_collections_abc", "_opcode_metadata", "_py_warnings", "_weakrefset",
    "abc", "annotationlib", "ast", "codeop", "collections", "contextlib",
    "copy", "copyreg", "dataclasses", "difflib", "dis", "enum", "functools", "genericpath",
    "heapq", "importlib", "importlib.machinery", "inspect", "io", "keyword", "linecache",
    "opcode", "operator", "os", "posixpath",
    "pprint", "re", "re._casefix", "re._compiler", "re._constants", "re._parser", "reprlib",
    "stat", "textwrap", "token", "tokenize", "traceback", "types", "typing", "unittest.case",
    "unittest.result", "unittest.util", "warnings", "weakref",
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def invoke(label, command, output, env, timeout):
    with (output / (label + ".log")).open("xb") as log:
        process = subprocess.Popen(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    if status:
        raise RuntimeError(f"{label} returned {status}. See {label}.log.")


def module_source(root, name, data, package=False):
    location = root / name.replace(".", "/")
    target = location / "__init__.py" if package else location.with_suffix(".py")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def prepare_packaging(archive, modules):
    """Use unchanged test bodies and expand existing pytest parameter fixtures ahead of guest execution."""
    if sha(archive) != PACKAGING_SHA:
        raise ValueError("PyPA packaging archive digest differs")
    base = "packaging-" + PACKAGING_REVISION + "/"
    with tarfile.open(archive, "r:gz") as upstream:
        for name in ("__init__", "_structures", "version"):
            data = upstream.extractfile(base + f"src/packaging/{name}.py").read()
            module = "packaging" if name == "__init__" else "packaging." + name
            modules[module] = (data, name == "__init__")
        raw = upstream.extractfile(base + "tests/test_version.py").read()
    text = raw.decode()
    lines = text.splitlines(keepends=True)
    parsed = ast.parse(text)
    guard = next(node for node in parsed.body if isinstance(node, ast.ClassDef) and node.name == "TestVersion")
    versions = next(node for node in parsed.body if isinstance(node, ast.Assign) and
                    any(isinstance(target, ast.Name) and target.id == "VERSIONS" for target in node.targets))
    version_inputs = ast.literal_eval(versions.value)
    parse = next(node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == "test_parse")
    replay = ["".join(lines[:5]), "import operator\nfrom packaging.version import Version, parse\n",
              "".join(lines[parse.lineno - 1:parse.end_lineno]), "\nclass TestVersion:\n"]
    cases = []
    skipped = ["test_parse_raises"]
    for node in guard.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            raise ValueError("unexpected test class source")
        if any(isinstance(item, ast.Name) and item.id in {"pytest", "pretend", "itertools"}
               for item in ast.walk(ast.Module(body=node.body, type_ignores=[]))):
            skipped.append(node.name)
            continue
        decorators = node.decorator_list
        if not decorators:
            arguments = [()]
        else:
            if (len(decorators) != 1 or ast.unparse(decorators[0].func) != "pytest.mark.parametrize"
                    or decorators[0].keywords):
                raise ValueError("unexpected upstream pytest decorator")
            parameters, fixture = decorators[0].args
            names = ast.literal_eval(parameters)
            if isinstance(fixture, ast.Name) and fixture.id == "VERSIONS":
                inputs = version_inputs
            else:
                try:
                    inputs = ast.literal_eval(fixture)
                except (TypeError, ValueError):
                    skipped.append(node.name)
                    continue
            arguments = [(arg,) for arg in inputs] if isinstance(names, str) else inputs
        replay.append("".join(lines[node.lineno - 1:node.end_lineno]))
        cases.append((node.name, arguments))
    replay.extend((
        "\ndef run():\n    test_parse()\n    tests = TestVersion()\n    count = 1\n",
        "    for name, matrix in " + repr(cases) + ":\n",
        "        for argv in matrix:\n            getattr(tests, name)(*argv)\n            count += 1\n",
        "    return count\n",
    ))
    modules["upstream_packaging_tests"] = ("".join(replay).encode(), False)
    return {"commit": PACKAGING_REVISION, "source_archive_sha256": PACKAGING_SHA,
            "upstream_tests_sha256": hashlib.sha256(raw).hexdigest(), "skipped": skipped,
            "invocations": 1 + sum(len(args) for _, args in cases), "test_methods": 1 + len(cases)}


def add_stdlib(archive, modules):
    """Bundle the actual selected CPython library sources from the same pinned release."""
    if sha(archive) != CPYTHON_SHA:
        raise ValueError("CPython source archive digest differs")
    with tarfile.open(archive, "r:xz") as upstream:
        base = "Python-3.14.8/Lib/"
        sources = {member.name[len(base):]: member for member in upstream if member.isfile()
                   and member.name.startswith(base) and member.name.endswith(".py")}
        for name in STDLIB:
            stem = name.replace(".", "/")
            package = stem + "/__init__.py" in sources
            relative = stem + ("/__init__.py" if package else ".py")
            modules[name] = (upstream.extractfile(sources[relative]).read(), package)
    # The normal __init__ also loads a signal-aware CLI. The guest calls the
    # exact TestCase and TestResult implementation directly, with no CLI.
    modules["unittest"] = (b"from .case import TestCase\nfrom .result import TestResult\n", True)


def prepare(args):
    output = args.output
    output.mkdir(mode=0o700)
    if subprocess.check_output(["/usr/bin/git", "-C", args.angles, "rev-parse", "HEAD"],
                               text=True).strip() != ANGLES_REVISION:
        raise ValueError("ROS angles revision differs")
    modules = {}
    for name, rel in (("angles", "angles/angles/__init__.py"), ("upstream_angles_tests", "angles/test/utest.py")):
        raw = subprocess.check_output(["/usr/bin/git", "-C", args.angles, "show", ANGLES_REVISION + ":" + rel])
        modules[name] = (raw, name == "angles")
    test = next(item for item in ast.parse(modules["upstream_angles_tests"][0]).body
                if isinstance(item, ast.ClassDef) and item.name == "TestAngles")
    names = [item.name for item in test.body if isinstance(item, ast.FunctionDef)
             and item.name.startswith("test_")]
    if len(names) != 7:
        raise ValueError("unexpected ROS angles test inventory")
    packaging = prepare_packaging(args.packaging, modules)
    extra = list(modules)
    add_stdlib(args.cpython, modules)
    report = {
        "angles": {"commit": ANGLES_REVISION, "methods": names,
                   "test_source_sha256": hashlib.sha256(modules["upstream_angles_tests"][0]).hexdigest()},
        "packaging": packaging,
        "stdlib_archive_sha256": CPYTHON_SHA, "complete": False, "engines": {},
    }
    native = output / "native"
    native.mkdir()
    bot = ("from unittest import TestResult\nfrom upstream_angles_tests import TestAngles\n"
           "from upstream_packaging_tests import run\n"
           "result = TestResult()\n"
           f"for name in {names!r}:\n    TestAngles(name).run(result)\n"
           f"assert result.testsRun == {len(names)}\n"
           "assert result.wasSuccessful() and not result.skipped, (result.errors, result.failures)\n"
           "assert run() == " + str(packaging["invocations"]) + "\n")
    native_entry = native / "replay.py"
    native_entry.write_text("import sys\nsys.path.insert(0, " + repr(str(native)) + ")\n" + bot)
    for name in extra:
        source, package = modules[name]
        module_source(native, name, source, package)
    guest = output / "bundle"
    paths = {name: module_source(guest, name, source, package)
             for name, (source, package) in modules.items()}
    guest_entry = output / "main.py"
    guest_entry.write_text("import sys\nassert sys.implementation.name == 'cpython'\n"
                           "assert sys.version_info[:3] == (3, 14, 8) and sys.maxsize == 2**31 - 1\n" + bot)
    return report, native_entry, guest_entry, paths


def test(args):
    from guest_profile import Profile
    from imports import inspect
    import qualification
    import runtime_pack
    from compiler import make_command
    from separate_compilation import cgroup_record

    group = cgroup_record()
    if ".tmp" not in args.output.parts:
        raise ValueError("choose a new output directory under .tmp")
    report, native, guest, bundled = prepare(args)
    report["cgroup"] = group
    vm_sha = sha(args.vm)
    report["vm_sha256"] = vm_sha
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result_path = args.output / "results.json"
    try:
        invoke("native-reference", [sys.executable, "-I", "-S", "-B", native], args.output, env, 15)
        report["native_reference"] = "passed"
        site_path = args.sdk / qualification.local_release.SITE
        site = qualification.local_release.parse_site(site_path.read_bytes())
        if qualification.check_site(site_path.read_bytes(), args.sdk, "c") != site["release_sha256"]:
            raise ValueError("installed signed C site selection differs")
        release = qualification.select_site_release(
            qualification.local_release.verified_releases(site["trust"]), "c", site["release_sha256"],
        )
        profile = Profile(32, "3.0", False, True, "eh")
        if (release["profile"] != profile.to_dict() or release["settings"] != {"optimization": "3", "debug": True}
                or release["vm_sha256"] != vm_sha):
            raise ValueError("installed C site does not qualify this exact compiler profile and VM")
        _, closure = make_command(Path(site["toolchain"]), list(map(Path, site["sysroots"])),
                                  profile, "c", ["-c"], verify=True)
        expected = runtime_pack.identity(profile, closure)
        saved = json.loads((runtime_pack.DIST / (profile.identity + ".json")).read_bytes())
        if any(saved.get(key) != value for key, value in expected.items()):
            raise ValueError("exact CPython runtime pack does not match the installed SDK closure")
        report["site_sha256"] = sha(site_path)
        report["site_release_sha256"] = site["release_sha256"]
        report["runtime_pack_sha256"] = saved["sha256"]
        wasm = args.output / "upstream.wasm"
        options = [entry for name, path in bundled.items() for entry in ("--module", name + "=" + str(path))]
        invoke("compile", [sys.executable, "-I", "-B", args.sdk / "bin/wrpy", guest,
                           "--target", "wasm32", "--build-receipt", *options, "-o", wasm], args.output, env, 100)
        proof_file = wasm.with_suffix(".wasm.wros-build.json")
        proof = json.loads(proof_file.read_bytes())
        expected_imports = {("wasi_snapshot_preview1", "clock_time_get"), ("wasi_snapshot_preview1", "clock_res_get")}
        if (proof["mode"] != "strict" or proof["release_sha256"] != site["release_sha256"]
                or proof["artifact_sha256"] != sha(wasm) or proof["vm_sha256"] != vm_sha
                or {(i["module"], i["name"]) for i in inspect(wasm.read_bytes())} != expected_imports):
            raise ValueError("guest imports or exact signed compiler receipt differ")
        runtime_note = json.loads(wasm.with_suffix(".wasm.wros-py.json").read_bytes())
        if (runtime_note["interpreter_archive_sha256"] != saved["archive_sha256"]
                or runtime_note["wasm_sha256"] != proof["artifact_sha256"]):
            raise ValueError("interpreter artifact differs from the approved exact closure")
        report.update(wasm_sha256=proof["artifact_sha256"], imports=sorted(expected_imports))
        clocks = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main"]
        for _, name in sorted(expected_imports):
            clocks += ["--wasip1-single-interface", "main", name, "allow"]
        for grant in ("realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution"):
            clocks += ["--wasip1-single-grant", "main", grant]
        for engine in ("int", "aot"):
            command = [args.vm, *profile.uwvm_feature_flags(), "--runtime-" + engine,
                       "--runtime-compile-threads", "3", "--runtime-llvm-jit-cache-path", "disable",
                       "--runtime-llvm-jit-full-policy", "legacy-light", "--wasm-set-main-module-name", "main",
                       "--runtime-memtag-mode", "sync", "--debug-fault-action", "exit", *clocks, "--run", wasm]
            invoke(engine, command, args.output, env, 170)
            report["engines"][engine] = "passed"
        report["complete"] = True
    except Exception as exc:
        report["failure"] = str(exc)
        raise
    finally:
        result_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for path in ("angles", "packaging", "cpython", "sdk", "vm", "output"):
        parser.add_argument("--" + path, type=lambda p: Path(p).resolve(), required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.sdk / "install"))
    sys.path.insert(0, str(args.sdk / "language/py"))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    test(args)
