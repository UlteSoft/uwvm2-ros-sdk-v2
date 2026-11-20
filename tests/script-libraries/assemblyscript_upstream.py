"""@file assemblyscript_upstream.py
@brief Replay pinned upstream AssemblyScript NativeMath assertions in installed guests.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import tarfile
import tempfile

from upstream_libraries import run, sha, verified_member

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS))
from separate_compilation import cgroup_record, inspect

ROOT = TESTS.parent
UPSTREAM = "b6bda05c29c9eb7d07d7f6cb2703508483b30493"
ARCHIVE = "1b89b3940f2287f8dd5487effe8332479bb94a0272beb47c583dade744949792"

WRAPPER = """
function assert(condition: bool): void {
  if (!condition) unreachable();
}
export function imul(left: f64, right: f64): f64 {
  return NativeMath.imul(left, right);
}
export function clz32(value: f64): f64 {
  return NativeMath.clz32(value);
}
export function _start(): void {
"""


def replay(args, group):
    """@brief Verify source integrity, final guest shape, and arithmetic results."""
    library, tests = "std/assembly/math.ts", "tests/compiler/std/math.ts"
    source = verified_member(args.upstream, ARCHIVE, "assemblyscript-" + UPSTREAM,
                             (library, tests, "LICENSE"))
    tests_text = "".join(line for line in source[tests].splitlines(keepends=True)
                         if re.match(r"^assert\(NativeMath\.(imul|clz32)\(", line))
    if tests_text.count("\n") != 28:
        raise ValueError("unexpected upstream assertion inventory")
    args.output.mkdir(mode=0o700)
    reference = args.output / "reference.cjs"
    harness = Path(__file__).with_name("assemblyscript_math.cjs").read_text()
    reference.write_text("function checkOriginal(NativeMath, f64, assert) {\n" + tests_text + "}\n" + harness)
    (args.output / "upstream-LICENSE").write_text(source["LICENSE"])
    program = args.output / "math.ts"
    program.write_text(WRAPPER + tests_text + """
  assert(imul(-0.5, 1.0) == 0.0);
  assert(imul(-1.5, 1.0) == -1.0);
  assert(clz32(-0.5) == 32.0);
}
""")
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(args.output),
           "PYTHONDONTWRITEBYTECODE": "1"}
    result = {"complete": False, "sdk_commit": args.commit, "vm_sha256": sha(args.vm),
              "cgroup": group, "upstream_commit": UPSTREAM, "archive_sha256": ARCHIVE, "engines": {}}
    result["sources"] = {name: hashlib.sha256(content.encode()).hexdigest() for name, content in source.items()}
    result_file = args.output / "results.json"
    try:
        with tempfile.TemporaryDirectory(dir=args.output) as scratch:
            prefix = Path(scratch) / "sdk"
            run([sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install", "--local-repository", ROOT,
                 "--commit", args.commit, "--platform", "unitree", "--language", "as", "--prefix", prefix],
                args.output, env, "install", 110)
            record = json.loads((args.output / "install.log").read_bytes())
            if record["commit"] != args.commit:
                raise ValueError("unexpected installed SDK revision")
            sdk = Path(record["directory"])
            cache = prefix / ".objects"
            if cache.is_dir():
                shutil.rmtree(cache)
            with tarfile.open(sdk / "third-parties/assemblyscript/compiler.tar.xz", "r:xz") as bundle:
                with bundle.extractfile("node_modules/assemblyscript/" + library) as math:
                    if hashlib.file_digest(math, "sha256").hexdigest() != result["sources"][library]:
                        raise ValueError("installed SDK math.ts differs from the pinned upstream source")
            artifact = args.output / "math.wasm"
            run([sdk / "bin/wras", "-g", "--build-receipt", program, "-o", artifact],
                args.output, env, "compile", 80)

        proof = json.loads(Path(str(artifact) + ".wros-as.json").read_bytes())
        identity = sha(artifact)
        imports = inspect(artifact.read_bytes())
        if (proof["profile"] != "register-only-wasm32" or proof["mte_requested"] is not True
                or proof["linear_memories"] != 0 or imports or proof["wasm_sha256"] != identity
                or proof["source_sha256"] != sha(program)):
            raise ValueError("unexpected scalar profile")
        run([args.wabt, artifact], args.output, env, "disassembly", 10)
        disassembly = (args.output / "disassembly.log").read_text()
        arithmetic = ("i32.clz", "i32.mul", "i32.trunc_sat_f64_s")
        if (not all(op in disassembly for op in arithmetic)
                or any(section in disassembly for section in ("(memory ", "(import ", "(data "))):
            raise ValueError("unexpected optimized instructions or section in scalar math Wasm")
        result.update(wasm_sha256=identity, wasm_bytes=artifact.stat().st_size, imports=imports,
                      linear_memories=0, instructions=arithmetic, mte_requested=True)
        for engine in ("int", "aot"):
            run([args.vm, "-WF3", "--wasm-feature-disable-exceptions", "--wasm-feature-disable-threads",
                 "--runtime-" + engine,
                 "--runtime-compile-threads", "0", "--runtime-memtag-mode", "sync",
                 "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit", "--run", artifact],
                args.output, env, engine, 30)
            result["engines"][engine] = "passed"
        run([args.node, reference, artifact], args.output, env, "reference", 20)
        result["native_control"] = json.loads((args.output / "reference.log").read_bytes())
        if result["native_control"] != {"upstream_assertions": 28, "differential_checks": 4100}:
            raise ValueError("unexpected numerical comparison inventory")
        result["complete"] = True
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        result["failure"] = str(error)
        raise
    finally:
        result_file.write_text(json.dumps(result, indent=2) + "\n")


def main():
    """@brief Run with the same 64 GiB gate as the remaining SDK acceptance tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for field in ("upstream", "vm", "output"):
        parser.add_argument("--" + field, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--wabt", type=Path, default=Path("/usr/bin/wasm2wat"))
    parser.add_argument("--node", type=Path, default=Path("/usr/bin/node"))
    args = parser.parse_args()
    if ".tmp" not in args.output.parts:
        parser.error("choose a fresh output directory inside .tmp")
    group = cgroup_record()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    replay(args, group)


if __name__ == "__main__":
    main()
