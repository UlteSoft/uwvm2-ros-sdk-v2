"""@brief Exercise the installed standard-Go producer and real VM engine entry points."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

CASES = """package robot
func Gain(x, scale, bias int32) int32 { return x*scale + bias }
func Subtract(left, right uint64) uint64 { return left-right }
func Before(a,b int64) bool { return a < b }
func Mask(a,b uint32) uint32 { return (a^b) | (a&b) }
func Start() uint32 { return 0 }
"""
CONSUMER = """(module
 (import "algorithm" "Gain" (func $gain (param i32 i32 i32) (result i32)))
 (import "algorithm" "Subtract" (func $sub (param i64 i64) (result i64)))
 (import "algorithm" "Before" (func $before (param i64 i64) (result i32)))
 (import "algorithm" "Mask" (func $mask (param i32 i32) (result i32)))
 (func (export "_start")
  (if (i32.ne (call $gain (i32.const 2147483647) (i32.const 2) (i32.const 3)) (i32.const 1)) (then unreachable))
  (if (i64.ne (call $sub (i64.const 4) (i64.const 6)) (i64.const -2)) (then unreachable))
  (if (i32.eqz (call $before (i64.const -2) (i64.const 1))) (then unreachable))
  (if (i32.ne (call $mask (i32.const 10) (i32.const 6)) (i32.const 14)) (then unreachable))))"""
NEGATIVE = {
    "pointer": "func Bad(p *int32) int32 { return *p }",
    "slice": "func Bad(p []int32) int32 { return p[0] }",
    "global": "var mutable int32",
    "heap": "func Bad() *int32 { return new(int32) }",
    "goroutine": "func Bad() int32 { go func(){}(); return 1 }",
    "conditional": "func Bad(x uint32) uint32 { if x>2 { return x*x }; return x }",
    "directive": "//go:noinline\nfunc Bad() uint32 { return 1 }",
    "bad-type": "func Bad() uint32 { return false }",
    "import": 'import "unsafe"',
}


def digest(path):
    """@brief Return the content digest of one qualification artifact."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    """@brief Build actual guests and retain each test outcome in the output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", required=True, type=Path)
    parser.add_argument("--vm", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wat2wasm", type=Path, required=True)
    parser.add_argument("--xmake", type=Path, required=True)
    args = parser.parse_args()
    root, work = args.sdk.resolve(), args.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    tool = root / "bin/wrgo"
    rows = []
    env = dict(os.environ, PATH="/usr/bin:/bin", UWVM_ROS_SDK_ROOT=str(root),
               WROS_VM=str(args.vm), WROS_PLATFORM=root.parents[1].name,
               XMAKE_GLOBALDIR=str(work / "xmake-global"))
    env.pop("WROS_RUN_QUERIES", None)

    def run(name, argv, *, success=True, cwd=work, environ=env):
        output = work / (name + ".log")
        with output.open("wb") as log:
            proc = subprocess.run(argv, cwd=cwd, env=environ, stdout=log,
                                  stderr=subprocess.STDOUT, timeout=120)
        rows.append(dict(name=name, exit=proc.returncode, sha256=digest(output)))
        if (proc.returncode == 0) != success:
            raise RuntimeError(name + " failed: " + output.read_text(errors="replace")[-1500:])

    def vm(engine, guest, extra=()):
        return [args.vm, "--runtime-" + engine, "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                "--wasm-set-main-module-name", "main", *extra, "--run", guest]

    source, guest = work / "compute.go", work / "algorithm.wasm"
    source.write_text(CASES)
    run("compile-default", [tool, source, "-o", guest, "--build-receipt"])
    record = json.loads(Path(str(guest) + ".wros-go.json").read_bytes())
    assert record["mte_requested"] and record["linear_memories"] == 0 and not record["wasm_imports"]
    assert record["wasm_sha256"] == digest(guest) and record["source_sha256"] == digest(source)
    off = work / "off.wasm"
    run("explicit-no-mte", [tool, source, "--no-mte", "-o", off, "--build-receipt"])
    assert not json.loads(Path(str(off) + ".wros-go.json").read_bytes())["mte_requested"]
    assert off.read_bytes() == guest.read_bytes()
    for case, definition in NEGATIVE.items():
        source.write_text("package robot\n" + definition + "\nfunc Start() uint32 { return 0 }\n")
        run("reject-" + case, [tool, source, "-o", guest], success=False)
        assert digest(guest) == record["wasm_sha256"]
    source.write_text(CASES)
    run("reject-memory64", [tool, source, "--target", "wasm64", "-o", guest], success=False)
    run("reject-threads", [tool, source, "-pthread", "-o", guest], success=False)
    (work / "calls.wat").write_text(CONSUMER)
    consumer = work / "calls.wasm"
    run("compile-consumer", [args.wat2wasm, work / "calls.wat", "-o", consumer])
    for engine in ("int", "aot"):
        run(engine + "-arithmetic", vm(engine, consumer, ["--wasm-preload-library", guest, "algorithm"]))
    artifacts = {"arithmetic": digest(guest), "consumer": digest(consumer)}
    for kind in ("common", "extension", "migration"):
        project = work / kind
        shutil.copytree(root / "examples/shared" / kind / "go", project)
        opts = dict(env, WROS_RUN_QUERIES="abi") if kind == "extension" else env
        run(kind + "-config", [args.xmake, "f", "-p", "wasm-wasip1", "-a", "wasm32"], cwd=project, environ=opts)
        run(kind + "-build", [args.xmake, "build"], cwd=project, environ=opts)
        run(kind + "-test", [args.xmake, "test", "-j1"], cwd=project, environ=opts)
        module, = project.rglob("controller.wasm")
        artifacts[kind] = digest(module)
        if kind == "extension":
            for engine in ("int", "aot"):
                run(engine + "-deny", vm(engine, module), success=False)
                if "ROS scene interface is hidden" not in (work / (engine + "-deny.log")).read_text():
                    raise ValueError("guest failed without the expected ROS permission denial")
    (work / "results.json").write_text(json.dumps(dict(scope="standard-Go register-only wasm32",
        vm_sha256=digest(args.vm), test_sha256=digest(Path(__file__)), artifacts=artifacts, compiler=json.loads((root / "language/go/release.json").read_bytes()),
        cases=rows), indent=2) + "\n")


if __name__ == "__main__":
    main()
