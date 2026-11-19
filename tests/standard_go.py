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
func Clamp(x int32) int32 {
    if x < -2 { return -2 }
    if x > 6 { return 6 }
    return x
}
func Calibrated(x, bias int64, invert bool) int64 {
    out := x+bias
    if invert { out = bias-x } else { out *= 3 }
    return out+7
}
func Valid(armed, fresh, stopped bool) bool { return armed && fresh && !stopped }
func Field(value uint32, shift uint64) uint32 { return value >> shift }
func SignedField(value int64, shift uint32) int64 { return value >> shift }
func Flag(value uint64, shift uint64) uint64 { return value << shift }
func Rotate(value uint32) uint32 { return value << 27 | value >> 5 }
func Narrow(value int64) int32 { return int32(value) }
func Widen(value int32) uint64 { return uint64(value) }
func UnsignedValue(value int32) uint32 { return uint32(value) }
func ConvertCount(value uint32, shift int32) uint32 { return value >> uint32(shift) }
func ConvertBranch(first int32, second uint32, choose bool) uint32 {
    if choose { second = uint32(first) }
    return second
}
func SignedScale(value int32) int32 { return value / 7 }
func SignedBucket(value int32) int32 { return value % -37 }
func WideScale(value int64) int64 { return value / 7 }
func UnsignedBucket(value uint64) uint64 { return value % 18446744073709551615 }
func Flip(value int64) int64 { return value / -1 }
func RemainderUnit(value int64) int64 { return value % -1 }
func Start() uint32 { return 0 }
"""
CONSUMER = """(module
 (import "algorithm" "Gain" (func $gain (param i32 i32 i32) (result i32)))
 (import "algorithm" "Subtract" (func $sub (param i64 i64) (result i64)))
 (import "algorithm" "Before" (func $before (param i64 i64) (result i32)))
 (import "algorithm" "Mask" (func $mask (param i32 i32) (result i32)))
 (import "algorithm" "Clamp" (func $clamp (param i32) (result i32)))
 (import "algorithm" "Calibrated" (func $calibrate (param i64 i64 i32) (result i64)))
 (import "algorithm" "Valid" (func $valid (param i32 i32 i32) (result i32)))
 (import "algorithm" "Field" (func $field (param i32 i64) (result i32)))
 (import "algorithm" "SignedField" (func $signed (param i64 i32) (result i64)))
 (import "algorithm" "Flag" (func $flag (param i64 i64) (result i64)))
 (import "algorithm" "Rotate" (func $rotate (param i32) (result i32)))
 (import "algorithm" "Narrow" (func $narrow (param i64) (result i32)))
 (import "algorithm" "Widen" (func $widen (param i32) (result i64)))
 (import "algorithm" "UnsignedValue" (func $unsigned (param i32) (result i32)))
 (import "algorithm" "ConvertCount" (func $count (param i32 i32) (result i32)))
 (import "algorithm" "ConvertBranch" (func $branch (param i32 i32 i32) (result i32)))
 (import "algorithm" "SignedScale" (func $scale32 (param i32) (result i32)))
 (import "algorithm" "SignedBucket" (func $bucket32 (param i32) (result i32)))
 (import "algorithm" "WideScale" (func $scale64 (param i64) (result i64)))
 (import "algorithm" "UnsignedBucket" (func $bucket64 (param i64) (result i64)))
 (import "algorithm" "Flip" (func $flip (param i64) (result i64)))
 (import "algorithm" "RemainderUnit" (func $unit (param i64) (result i64)))
 (func (export "_start")
  (if (i32.ne (call $gain (i32.const 2147483647) (i32.const 2) (i32.const 3)) (i32.const 1)) (then unreachable))
  (if (i64.ne (call $sub (i64.const 4) (i64.const 6)) (i64.const -2)) (then unreachable))
  (if (i32.eqz (call $before (i64.const -2) (i64.const 1))) (then unreachable))
  (if (i32.ne (call $mask (i32.const 10) (i32.const 6)) (i32.const 14)) (then unreachable))
  (if (i32.ne (call $clamp (i32.const -2147483648)) (i32.const -2)) (then unreachable))
  (if (i32.ne (call $clamp (i32.const 3)) (i32.const 3)) (then unreachable))
  (if (i32.ne (call $clamp (i32.const 2147483647)) (i32.const 6)) (then unreachable))
  (if (i64.ne (call $calibrate (i64.const 4) (i64.const 11) (i32.const 0)) (i64.const 52)) (then unreachable))
  (if (i64.ne (call $calibrate (i64.const 4) (i64.const 11) (i32.const 1)) (i64.const 14)) (then unreachable))
  (if (i64.ne (call $calibrate (i64.const 9223372036854775807) (i64.const 0) (i32.const 0))
                  (i64.const -9223372036854775804)) (then unreachable))
  (if (i32.ne (call $valid (i32.const 3) (i32.const 2) (i32.const 0)) (i32.const 1)) (then unreachable))
  (if (call $valid (i32.const 0) (i32.const 1) (i32.const 0)) (then unreachable))
  (if (call $valid (i32.const 1) (i32.const 0) (i32.const 0)) (then unreachable))
  (if (call $valid (i32.const 1) (i32.const 1) (i32.const 9)) (then unreachable))
  (if (i32.ne (call $field (i32.const -1) (i64.const 31)) (i32.const 1)) (then unreachable))
  (if (call $field (i32.const -1) (i64.const 4294967296)) (then unreachable))
  (if (i64.ne (call $signed (i64.const -19) (i32.const -1)) (i64.const -1)) (then unreachable))
  (if (i64.ne (call $signed (i64.const 19) (i32.const -1)) (i64.const 0)) (then unreachable))
  (if (i64.ne (call $flag (i64.const 7) (i64.const 64)) (i64.const 0)) (then unreachable))
  (if (i32.ne (call $rotate (i32.const 32)) (i32.const 1)) (then unreachable))
  (if (i32.ne (call $narrow (i64.const 4294967297)) (i32.const 1)) (then unreachable))
  (if (i64.ne (call $widen (i32.const -1)) (i64.const -1)) (then unreachable))
  (if (i32.ne (call $unsigned (i32.const -1)) (i32.const -1)) (then unreachable))
  (if (call $count (i32.const -1) (i32.const -1)) (then unreachable))
  (if (i32.ne (call $branch (i32.const -11) (i32.const 92) (i32.const 1)) (i32.const -11)) (then unreachable))
  (if (i32.ne (call $branch (i32.const -11) (i32.const 92) (i32.const 0)) (i32.const 92)) (then unreachable))
  (if (i32.ne (call $scale32 (i32.const -99)) (i32.const -14)) (then unreachable))
  (if (i32.ne (call $bucket32 (i32.const -75)) (i32.const -1)) (then unreachable))
  (if (i64.ne (call $scale64 (i64.const -99)) (i64.const -14)) (then unreachable))
  (if (i64.ne (call $bucket64 (i64.const -1)) (i64.const 0)) (then unreachable))
  (if (i64.ne (call $bucket64 (i64.const -2)) (i64.const -2)) (then unreachable))
  (if (i64.ne (call $flip (i64.const -9223372036854775808)) (i64.const -9223372036854775808)) (then unreachable))
  (if (i64.ne (call $unit (i64.const -9223372036854775808)) (i64.const 0)) (then unreachable))))"""
NEGATIVE = {
    "pointer": "func Bad(p *int32) int32 { return *p }",
    "slice": "func Bad(p []int32) int32 { return p[0] }",
    "global": "var mutable int32",
    "heap": "func Bad() *int32 { return new(int32) }",
    "goroutine": "func Bad() int32 { go func(){}(); return 1 }",
    "loop": "func Bad(x uint32) uint32 { for x > 0 { x-- }; return x }",
    "runtime-panic": "func Bad(x uint32) uint32 { if x > 0 { panic(\"sensor\") }; return x }",
    "directive": "//go:noinline\nfunc Bad() uint32 { return 1 }",
    "bad-type": "func Bad() uint32 { return false }",
    "possibly-negative-shift": "func Bad(x uint32, count int32) uint32 { return x >> count }",
    "nonconstant-divisor": "func Bad(x, y int64) int64 { return x / y }",
    "zero-divisor": "func Bad(x uint64) uint64 { return x % 0 }",
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
    debug = work / "algorithm-debug.wasm"
    run("compile-source-map", [tool, source, "-g", "-o", debug, "--build-receipt"])
    debug_record = json.loads(Path(str(debug) + ".wros-go.json").read_bytes())
    assert debug_record["debug_metadata"] == "source-map-v3"
    debug_bytes = debug.read_bytes()
    guest_bytes = guest.read_bytes()
    assert debug_bytes.startswith(guest_bytes) and b".debug_source_map" in debug_bytes[len(guest_bytes):]
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
    artifacts = {"arithmetic": digest(guest), "debug": digest(debug), "consumer": digest(consumer)}
    for kind in ("common", "extension", "migration"):
        project = work / kind
        shutil.copytree(root / "examples/shared" / kind / "go", project)
        if kind == "common":
            config = project / "xmake.lua"
            config.write_text(config.read_text().replace('    set_kind("binary")',
                                                          '    set_kind("binary")\n    set_symbols("debug")'))
        opts = dict(env, WROS_RUN_QUERIES="abi") if kind == "extension" else env
        run(kind + "-config", [args.xmake, "f", "-p", "wasm-wasip1", "-a", "wasm32"], cwd=project, environ=opts)
        run(kind + "-build", [args.xmake, "build"], cwd=project, environ=opts)
        run(kind + "-test", [args.xmake, "test", "-j1"], cwd=project, environ=opts)
        module, = project.rglob("controller.wasm")
        artifacts[kind] = digest(module)
        if kind == "common":
            assert b".debug_source_map" in module.read_bytes()
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
