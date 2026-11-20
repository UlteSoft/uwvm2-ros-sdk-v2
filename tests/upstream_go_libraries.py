"""@file upstream_go_libraries.py
@brief Run the original xxHash library and upstream functional assertions in a strict TinyGo guest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ("sdk", "source", "site", "vm", "output"):
    parser.add_argument("--" + name, required=True, type=lambda value: Path(value).resolve())
parser.add_argument("--commit", required=True)
args = parser.parse_args()
sdk, source, vm, out = args.sdk, args.source, args.vm, args.output
sys.path[:0] = [str(sdk / "tests"), str(sdk / "install")]
from separate_compilation import cgroup_record
from bootstrap import Source, install
from guest_profile import Profile
from imports import inspect

group = cgroup_record()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
revision = args.commit
upstream = "998dce232f17418a7a5721ecf87ca714025a3243"
env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "GO"))}
env.update(PATH="/usr/bin:/bin", LC_ALL="C", TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
assert subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip() == upstream
assert not subprocess.check_output(["git", "-C", source, "status", "--porcelain"])

out.mkdir(mode=0o700)
project = out / "project"
dep = project / "xxhash"
shutil.copytree(source, dep, ignore=shutil.ignore_patterns(".git"))
original = (dep / "xxhash_test.go").read_text()
marker = "func TestAllocs("
assert original.count(marker) == 1 and original.count('"testing"') == 1
test_cases = original.split(marker, 1)[0].replace('"testing"', '"github.com/cespare/xxhash/v2/testshim"')
tests = ("TestAll", "TestReset", "TestResetWithSeed", "TestBinaryMarshaling")
assert re.findall(r"(?m)^func (Test\w+)\(", test_cases) == list(tests)
(dep / "wros_upstream_cases.go").write_text(test_cases)
(dep / "testshim").mkdir()
(dep / "testshim/testing.go").write_text('''package testing
type T struct { Runs uint32 }
func (t *T) Run(_ string, f func(*T)) bool { t.Runs++; f(t); return true }
func (t *T) Fatalf(_ string, _ ...interface{}) { panic("upstream assertion failed") }
func (t *T) Errorf(format string, args ...interface{}) { t.Fatalf(format, args...) }
func (t *T) Fatal(_ ...interface{}) { panic("upstream assertion failed") }
''')
(project / "go.mod").write_text('''module wros.local/xxhash-upstream
go 1.24
require github.com/cespare/xxhash/v2 v2.3.0
replace github.com/cespare/xxhash/v2 => ./xxhash
''')
(project / "main.go").write_text('''package main
import "github.com/cespare/xxhash/v2"
import "github.com/cespare/xxhash/v2/testshim"
func main() {
    t := &testing.T{}
    xxhash.TestAll(t)
    xxhash.TestReset(t)
    xxhash.TestResetWithSeed(t)
    xxhash.TestBinaryMarshaling(t)
    if t.Runs != 148 { panic("upstream subtest count differs") }
}
''')
source_store = Source(revision, sdk)
installation = Path(install(source_store, "unitree", "tinygo", out / "sdk", [], site_profile=args.site)["directory"])
toolchain = Path(json.loads(args.site.read_text())["toolchain"])
host_go = toolchain / "libexec/wros/go/bin/go"
result = {"complete": False, "cgroup": group, "sdk_commit": revision, "upstream_commit": upstream,
          "full_test_source_sha256": hashlib.sha256(original.encode()).hexdigest(),
          "guest_test_source_sha256": hashlib.sha256(test_cases.encode()).hexdigest(),
          "upstream_tests": tests, "subtests": 148, "outcomes": {}}
env.update(GOPROXY="off", GOSUMDB="off", GOTOOLCHAIN="local", CGO_ENABLED="0",
           GOMODCACHE=str(out / "go-modules"), GOCACHE=str(out / "go-cache"))

def write():
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")

def run(label, argv, *, cwd=project):
    process = subprocess.run(list(map(str, argv)), env=env, cwd=cwd, capture_output=True, timeout=300)
    (out / (label + ".log")).write_bytes(process.stdout + process.stderr)
    result["outcomes"][label] = {"exit": process.returncode}
    write()
    if process.returncode:
        raise RuntimeError(label + " failed")

run("native-purego", [host_go, "test", "-p", "4", "-tags=purego", "-count=1", "-v", "."], cwd=source)
wasm = out / "xxhash.wasm"
run("wrtg", [installation / "bin/wrtg", project, "--build-receipt", "--print-identity", "-o", wasm])
binary = wasm.read_bytes()
receipt = json.loads(wasm.with_suffix(".wasm.wros-build.json").read_bytes())
profile = Profile(32, "3.0", False, True, "eh")
if (receipt["mode"] != "strict" or receipt["artifact_sha256"] != hashlib.sha256(binary).hexdigest()
        or receipt["profile"] != profile.to_dict() or receipt.get("vm_sha256") != hashlib.sha256(vm.read_bytes()).hexdigest()):
    raise ValueError("the Wasm guest must match the signed build profile and VM")
imports = inspect(binary)
clock = {"module": "wasi_snapshot_preview1", "name": "clock_time_get", "kind": 0,
         "params": ["i32", "i64", "i32"], "results": ["i32"]}
if imports != [clock]:
    raise ValueError("the upstream guest must import only the declared read-only clock")
permissions = ["--wasip1-single-create", "main", "--wasip1-single-enable", "main",
               "--wasip1-single-interface", "main", "clock_time_get", "allow",
               "--wasip1-single-grant", "main", "monotonic-clock",
               "--wasip1-single-grant", "main", "realtime-clock"]
for engine in ("int", "aot"):
    run(engine, [vm, *profile.uwvm_feature_flags(), "--runtime-memtag-mode", "sync",
                 "--runtime-" + engine, "--runtime-compile-threads", "0", "--wasm-set-main-module-name", "main",
                 "--runtime-llvm-jit-cache-path", "disable", "--debug-fault-action", "exit", *permissions, "--run", wasm])
result.update(complete=True, artifact_sha256=receipt["artifact_sha256"], vm_sha256=receipt["vm_sha256"], imports=imports)
write()
print("Pinned xxHash upstream functional assertions passed in both VM engines")
