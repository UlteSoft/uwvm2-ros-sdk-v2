"""@file upstream_libraries.py
@brief Replay pinned JavaScript and Ruby library tests through installed Wasm SDKs.
"""
import argparse
from contextlib import suppress
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile

SDK_COMMIT = "63b57f8b3debfe14cabd5af05de2ffbee22a0314"
BASEX_COMMIT = "b7b0cec52bf60d993957902e8e7c96906ac39c7c"
BASEX_ARCHIVE = "2647f68e4f94ef3c1cbed4ac51c7c59f0a65199fa6d3b9974a09ce5ca2112286"
ABBREV_COMMIT = "b362e8e3b92c48a9e8f34fc0f782d3396858db1f"
ABBREV_ARCHIVE = "56c8f82f13ecee86421988185302a6feea030ddbe2425123f0bba771b5afe24a"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verified_member(archive, digest, root, names):
    """Read bounded module, tests and fixtures from the pinned GitHub archive."""
    max_bytes = 5 * 1024 * 1024
    with archive.open("rb") as source:
        data = source.read(max_bytes + 1)
    if len(data) > max_bytes or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"archive differs from upstream pin: {archive.name}")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as stream:
        results = {}
        for name in names:
            entry = stream.getmember(root + "/" + name)
            if not entry.isfile() or entry.size > 512 * 1024:
                raise ValueError(f"unexpected upstream member: {name}")
            with stream.extractfile(entry) as source:
                results[name] = source.read().decode("utf-8")
        return results


def exact(text, old, new):
    if text.count(old) != 1:
        raise ValueError("unexpected published test or library layout")
    return text.replace(old, new, 1)


def run(argv, cwd, env, name, timeout):
    with (cwd / (name + ".log")).open("xb") as stream:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    if status:
        raise RuntimeError(f"{name} exited {status}. See {cwd / (name + '.log')}.")


JS_HARNESS = """
let assertions = 0, tests = 0;
function tape(name, body) {
  let planned = 0, actual = 0;
  const check = (pass) => {
    if (!pass) throw new Error(name);
    actual++;
  };
  body({
    plan(n) { if (planned !== 0 || n < 1) throw new Error(name); planned = n; },
    same(value, expected) { check(value === expected); },
    true(value) { check(value === true); },
    throws(action, expected) {
      let matches = false;
      try { action(); } catch (error) { matches = expected.test(String(error)); }
      check(matches);
    }
  });
  if (actual !== planned || planned === 0) throw new Error("assertion count: " + name);
  assertions += actual;
  tests++;
}
"""


def javascript(archive, output):
    """Replay the full original base-x suite with only its three module imports adapted."""
    root = "base-x-" + BASEX_COMMIT
    engine, tests, vectors, license_name = "src/esm/index.js", "test/index.js", "test/fixtures.json", "LICENSE.md"
    source = verified_member(archive, BASEX_ARCHIVE, root, (engine, tests, vectors, license_name))
    paths = {name: hashlib.sha256(data.encode()).hexdigest() for name, data in source.items()}
    engine_text = exact(source[engine], "export default base\n", "const basex = base;\n")
    current = source[tests]
    current = exact(current, "import basex from '../src/esm/index.js'\n", "")
    current = exact(current, "import tape from 'tape'\n", "")
    current = exact(current, "import fixtures from './fixtures.json' assert { type: 'json' }\n", "")
    fixtures = json.loads(source[vectors])
    positives, negatives = len(fixtures["valid"]), len(fixtures["invalid"])
    expected_assertions = positives * 2 + negatives + 5
    expected_tests = positives * 2 + negatives + 3
    script = output / "base-x.js"
    script.write_text(
        "/*\n" + source[license_name] + "*/\n" +
        engine_text + "const fixtures = " + source[vectors] + ";\n" + JS_HARNESS + "\n" + current +
        f"\nif (tests !== {expected_tests} || assertions !== {expected_assertions}) throw new Error('truncated suite');\n"
    )
    return script, script, {"commit": BASEX_COMMIT, "archive_sha256": BASEX_ARCHIVE,
                            "source_sha256": paths, "tests": expected_tests, "assertions": expected_assertions,
                            "valid_vectors": positives, "invalid_vectors": negatives}


RUBY_HARNESS = """
$assertions = 0
class WasmAssertions
  def assert_equal(expected, actual)
    raise "upstream expected equality" unless expected == actual
    $assertions += 1
  end
end
"""
RUBY_RUNNER = """
test = TestAbbrev.new
test.test_abbrev
test.test_abbrev_lf
raise "truncated upstream suite" unless $assertions == 6
"""


def ruby(archive, output):
    """Adapt literal-prefix filtering without a regexp gem and retain original assertions."""
    root = "abbrev-" + ABBREV_COMMIT
    engine, tests, license_name = "lib/abbrev.rb", "test/test_abbrev.rb", "LICENSE.txt"
    source = verified_member(archive, ABBREV_ARCHIVE, root, (engine, tests, license_name))
    paths = {name: hashlib.sha256(data.encode()).hexdigest() for name, data in source.items()}
    code = source[engine]
    adapted = exact(code, '    if pattern.is_a?(String)\n      pattern = /\\A#{Regexp.quote(pattern)}/  # regard as a prefix\n    end\n',
                    '    if pattern && !pattern.is_a?(String)\n      raise ArgumentError, "abbrev expects a literal string prefix"\n    end\n')
    for name in ("abbrev", "word"):
        adapted = exact(adapted, f"next if pattern && pattern !~ {name}",
                        f"next if pattern && {name}[0, pattern.size] != pattern")
    current = exact(source[tests], "require 'test/unit'\nrequire 'abbrev'\n", "")
    current = exact(current, "class TestAbbrev < Test::Unit::TestCase", "class TestAbbrev < WasmAssertions")
    native, guest = output / "abbrev-upstream.rb", output / "abbrev.rb"
    license_comments = "".join("# " + line + "\n" for line in source[license_name].splitlines())
    for path, engine_text in ((native, code), (guest, adapted)):
        path.write_text(license_comments + engine_text + RUBY_HARNESS + current + RUBY_RUNNER)
    return native, guest, {"commit": ABBREV_COMMIT, "archive_sha256": ABBREV_ARCHIVE,
                           "source_sha256": paths, "tests": 2, "assertions": 6,
                           "adaptation": "literal prefixes retain String semantics; other patterns are refused"}


def test(args, language, bootstrap, group):
    kind, executable, compiler, factory, archive = (
        ("base-x", "/usr/bin/node", "wrjs", javascript, args.basex) if language == "js" else
        ("abbrev", "/usr/bin/ruby", "wrrb", ruby, args.abbrev)
    )
    work = args.output / language
    work.mkdir(mode=0o700)
    env = {**os.environ, "PATH": "/usr/bin:/bin", "TMPDIR": str(work), "PYTHONDONTWRITEBYTECODE": "1"}
    state = {"complete": False, "phase": "source", "language": language, "library": kind,
             "cgroup": group, "sdk_commit": SDK_COMMIT, "vm_sha256": sha(args.vm), "engines": {}}
    try:
        native, script, source = factory(archive, work)
        state["upstream"] = source
        state["phase"] = "native"
        run([executable, native], work, env, "native", 20)
        state["native"] = "passed"
        if language == "ruby":
            run([executable, script], work, env, "native-adaptation", 20)
            state["native_adaptation"] = "passed"
        state["phase"] = "signed-installation"
        run([sys.executable, "-I", "-B", bootstrap, "install", "--local-repository", args.sdk,
             "--commit", SDK_COMMIT, "--platform", "unitree", "--language", language,
             "--prefix", work / "sdk", "--site-profile", args.site], work, env, "install", 150)
        install = json.loads((work / "install.log").read_bytes())
        sdk = Path(install["directory"])
        current_site = json.loads(args.site.read_bytes())
        state["site_sha256"] = sha(args.site)
        state["release_sha256"] = current_site["release_sha256"]
        state["phase"] = "compile"
        artifact = work / (kind + ".wasm")
        run([sys.executable, "-I", "-B", sdk / "bin" / compiler, "--target", "wasm32", "--build-receipt",
             script, "-o", artifact], work, env, "compile", 200)
        receipt = artifact.with_suffix(".wasm.wros-build.json")
        build = json.loads(receipt.read_bytes())
        identity = sha(artifact)
        if (build["mode"] != "strict" or build["artifact_sha256"] != identity
                or build["release_sha256"] != current_site["release_sha256"]
                or build["vm_sha256"] != state["vm_sha256"]
                or build["settings"] != {"optimization": "3", "debug": True}):
            raise ValueError("engine build does not match strict signed C closure")
        suffix = ".wasm.wros-js.json" if language == "js" else ".wasm.wros-ruby.json"
        engine_receipt = artifact.with_suffix(suffix)
        description = json.loads(engine_receipt.read_bytes())
        if description["script_sha256"] != sha(script) or description["wasm_sha256"] != identity:
            raise ValueError("language receipt differs from the executed module")
        expected = [["wasi_snapshot_preview1", "clock_time_get"]] if language == "js" else []
        verify = (
            "import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]);"
            "from imports import inspect; from guest_profile import Profile;"
            "p=Profile(32,'3.0',False,True,'eh');"
            "print(json.dumps(["
            "sorted([[i['module'],i['name']] for i in inspect(Path(sys.argv[2]).read_bytes())]),"
            "p.to_dict(),p.uwvm_feature_flags()]))"
        )
        run([sys.executable, "-I", "-B", "-c", verify, str(sdk / "install"), artifact],
            work, env, "inspect", 10)
        imports, profile, feature_flags = json.loads((work / "inspect.log").read_bytes())
        if imports != expected or build["profile"] != profile:
            raise ValueError("guest imports or ABI differ")
        state.update(wasm_sha256=identity, artifact_bytes=artifact.stat().st_size,
                     compiler_receipt_sha256=sha(receipt), interpreter_receipt_sha256=sha(engine_receipt),
                     imports=imports, profile=profile)
        clocks = (["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                   "--wasip1-single-interface", "main", "clock_time_get", "allow",
                   "--wasip1-single-grant", "main", "realtime-clock"] if language == "js" else [])
        for engine in ("int", "aot"):
            state["phase"] = engine
            flags = ["--runtime-llvm-jit-policy", "fast-compile"] if engine == "aot" else []
            run([args.vm, *feature_flags, "--wasm-set-main-module-name", "main", "--runtime-" + engine,
                 "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                 "--runtime-memtag-mode", "sync", "--debug-fault-action", "exit", *flags, *clocks,
                 "--run", artifact], work, env, engine, 170)
            state["engines"][engine] = "passed"
            print(kind, engine, "passed", flush=True)
        state.update(phase="completed", complete=True)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        state["failure"] = str(error)
    finally:
        (work / "results.json").write_text(json.dumps(state, indent=2) + "\n")
    return state


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from separate_compilation import cgroup_record

    parser = argparse.ArgumentParser(description=__doc__)
    for path in ("sdk", "vm", "site", "basex", "abbrev", "output"):
        parser.add_argument("--" + path, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--language", choices=("js", "ruby"), action="append")
    options = parser.parse_args()
    cgroup = cgroup_record()
    if ".tmp" not in options.output.parts:
        raise ValueError("choose a fresh output below .tmp")
    options.output.mkdir(mode=0o700)
    frozen = options.output / "bootstrap.py"
    frozen.write_bytes(subprocess.check_output(["/usr/bin/git", "-C", options.sdk, "show",
                                                SDK_COMMIT + ":install/bootstrap.py"]))
    observations = [test(options, language, frozen, cgroup) for language in options.language or ("js", "ruby")]
    passed = all(row["complete"] for row in observations)
    (options.output / "results.json").write_text(json.dumps({"complete": passed, "runs": observations}, indent=2) + "\n")
    raise SystemExit(0 if passed else 1)
