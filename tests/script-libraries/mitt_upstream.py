"""@file mitt_upstream.py
@brief Replay pinned upstream mitt's TypeScript and executable assertions through wrts.
"""
from argparse import ArgumentParser, Namespace
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from upstream_libraries import SDK_COMMIT, exact, run, sha, verified_member

MITT_COMMIT = "b240473b5707857ba2c6a8e6d707c28d1e39da49"
MITT_ARCHIVE = "5bfb7ae1c8674759d31684141a37e64914ac024b441dccda76775fc236039ced"


def prepare(args):
    """Keep the source and test bodies intact after rebinding framework/module imports."""
    source_name = "src/index.ts"
    test_name = "test/index_test.ts"
    types_name = "test/test-types-compilation.ts"
    sources = verified_member(args.mitt, MITT_ARCHIVE, "mitt-" + MITT_COMMIT,
                              (source_name, test_name, types_name, "LICENSE"))
    project = args.output / "project"
    (project / "src").mkdir(parents=True)
    (project / "test").mkdir()
    original_tests = sources[test_name]
    test_imports = (
        "import mitt, { Emitter, EventHandlerMap } from '..';\n"
        "import chai, { expect } from 'chai';\n"
        "import { spy } from 'sinon';\n"
        "import sinonChai from 'sinon-chai';\n"
        "chai.use(sinonChai);\n"
    )
    changes = {
        source_name: sources[source_name],
        test_name: exact(original_tests, test_imports,
                         "import mitt, { Emitter, EventHandlerMap } from '../src/index.js';\n"
                         "import { describe, it, beforeEach, expect, spy } from './harness.js';\n"),
        types_name: exact(sources[types_name], "import mitt from '..';", "import mitt from '../src/index.js';"),
        "test/harness.ts": args.harness.read_text(),
        "main.ts": (
            "import './test/index_test.js';\n"
            "import { verifyTotals } from './test/harness.js';\n"
            "verifyTotals(19, 43);\n"
        ),
    }
    for name, text in changes.items():
        (project / name).write_text(text)
    (project / "LICENSE").write_text(sources["LICENSE"])
    hashes = {name: hashlib.sha256(data.encode()).hexdigest() for name, data in sources.items()}
    files = [project / name for name in ("main.ts", source_name, test_name, types_name, "test/harness.ts")]
    assert sources[types_name].count("@ts-expect-error") == 10
    return project, files, hashes


def compare_native(sdk, project, files, output, env):
    """Use the SDK's pinned TypeScript compiler once for a separate native oracle."""
    loader = SourceFileLoader("wrts_oracle", str(sdk / "bin/wrts"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    texts, hashes = module.project(Namespace(sources=files, project_root=project))
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        stage = Path(temporary)
        compiler, node = module.compiler(stage)
        request = stage / "project.json"
        request.write_text(json.dumps(dict(sources=texts, entry=texts[0]["name"],
                                           declarations=module.sdk_declarations([]))))
        native = output / "native-control.js"
        run([node, "--jitless", "--single-threaded", "--no-addons", "--max-old-space-size=256",
             sdk / "language/typescript/compile.cjs", compiler, request, native],
            output, env, "native-compile", 90)
    run(["/usr/bin/node", native], output, env, "native-run", 15)
    return hashes, sha(native)


def test(args, group):
    state = {"complete": False, "phase": "preparing", "sdk_commit": SDK_COMMIT,
             "vm_sha256": sha(args.vm), "cgroup": group, "engines": {},
             "upstream": {"project": "mitt", "commit": MITT_COMMIT, "archive_sha256": MITT_ARCHIVE,
                          "tests": 19, "assertions": 43, "expected_type_errors": 10}}
    env = {**os.environ, "PATH": "/usr/bin:/bin", "TMPDIR": str(args.output), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        project, sources, upstream_hashes = prepare(args)
        state["upstream"]["source_sha256"] = upstream_hashes
        state["phase"] = "install"
        bootstrap = args.output / "bootstrap.py"
        bootstrap.write_bytes(subprocess.check_output(["/usr/bin/git", "-C", args.sdk, "show",
                                                       SDK_COMMIT + ":install/bootstrap.py"]))
        run([sys.executable, "-I", "-B", bootstrap, "install", "--local-repository", args.sdk,
             "--commit", SDK_COMMIT, "--platform", "unitree", "--language", "typescript",
             "--prefix", args.output / "sdk", "--site-profile", args.site],
            args.output, env, "install", 150)
        sdk = Path(json.loads((args.output / "install.log").read_bytes())["directory"])
        # The installation owns its file copies. This replay uses a private
        # prefix once, so it can discard the additional installer blob cache
        # before expanding the bundled Node and compiler distribution.
        cache = args.output / "sdk/.objects"
        if cache.is_dir():
            shutil.rmtree(cache)
        state["phase"] = "native"
        inputs, native_hash = compare_native(sdk, project, sources, args.output, env)
        state["native_control"] = "passed"
        state["native_javascript_sha256"] = native_hash
        state["phase"] = "compile"
        artifact = args.output / "mitt.wasm"
        run([sys.executable, "-I", "-B", sdk / "bin/wrts", "--project-root", project,
             "--target", "wasm32", "--build-receipt", *sources, "-o", artifact], args.output, env, "compile", 200)
        build = json.loads(artifact.with_suffix(".wasm.wros-build.json").read_bytes())
        ts_proof = json.loads(artifact.with_suffix(".wasm.wros-ts.json").read_bytes())
        js_receipt = artifact.with_suffix(".wasm.wros-js.json")
        js_proof = json.loads(js_receipt.read_bytes())
        identity = sha(artifact)
        expected_profile = json.loads(args.site.read_bytes())["release_sha256"]
        if (build["mode"] != "strict" or build["vm_sha256"] != state["vm_sha256"]
                or build["release_sha256"] != expected_profile or build["artifact_sha256"] != identity
                or build["settings"] != {"optimization": "3", "debug": True}
                or ts_proof["compiler"] != "TypeScript 5.9.3" or ts_proof["strict"] is not True
                or ts_proof["inputs"] != inputs or ts_proof["javascript_sha256"] != native_hash
                or ts_proof["interpreter_receipt_sha256"] != sha(js_receipt)
                or ts_proof["wasm_sha256"] != identity or js_proof["script_sha256"] != native_hash):
            raise ValueError("TypeScript, QuickJS and signed C compiler receipts disagree")
        state["phase"] = "import-audit"
        sys.path.insert(0, str(sdk / "install"))
        from imports import inspect
        from guest_profile import Profile
        profile = Profile(32, "3.0", False, True, "eh")
        imports = sorted((row["module"], row["name"]) for row in inspect(artifact.read_bytes()))
        if imports != [("wasi_snapshot_preview1", "clock_time_get")] or build["profile"] != profile.to_dict():
            raise ValueError("unexpected host imports or profile")
        state.update(wasm_sha256=identity, wasm_bytes=artifact.stat().st_size, imports=imports,
                     release_sha256=expected_profile, profile=profile.to_dict())
        clock = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
                 "--wasip1-single-interface", "main", "clock_time_get", "allow",
                 "--wasip1-single-grant", "main", "realtime-clock"]
        for engine in ("int", "aot"):
            state["phase"] = engine
            flags = ["--runtime-llvm-jit-policy", "fast-compile"] if engine == "aot" else []
            run([args.vm, *profile.uwvm_feature_flags(), "--wasm-set-main-module-name", "main",
                 "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                 "--runtime-memtag-mode", "sync", "--debug-fault-action", "exit", *flags, *clock,
                 "--run", artifact], args.output, env, engine, 170)
            state["engines"][engine] = "passed"
            print("mitt", engine, "passed", flush=True)
        state.update(complete=True, phase="completed")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        state["failure"] = str(error)
        raise
    finally:
        (args.output / "results.json").write_text(json.dumps(state, indent=2) + "\n")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from separate_compilation import cgroup_record

    parser = ArgumentParser(description=__doc__)
    for option in ("sdk", "site", "vm", "mitt", "output"):
        parser.add_argument("--" + option, required=True, type=lambda p: Path(p).resolve())
    opts = parser.parse_args()
    opts.harness = Path(__file__).with_name("mitt_harness.ts")
    group = cgroup_record()
    if ".tmp" not in opts.output.parts:
        raise ValueError("choose a new .tmp output")
    opts.output.mkdir(mode=0o700)
    test(opts, group)
