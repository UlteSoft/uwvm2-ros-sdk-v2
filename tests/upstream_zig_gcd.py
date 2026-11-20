"""@file upstream_zig_gcd.py
@brief Replay the official Zig gcd tests with dynamic differential checks.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tarfile
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
for option in ("sdk", "producer", "site32", "site64", "vm", "output"):
    parser.add_argument("--" + option, type=lambda p: Path(p).resolve(), required=True)
parser.add_argument("--commit", required=True)
args = parser.parse_args()
sdk, producer, site32, site64, vm, output = (args.sdk, args.producer, args.site32, args.site64, args.vm, args.output)
revision = args.commit
sys.path.insert(0, str(sdk / "tests"))
from separate_compilation import Profile, cgroup_record, inspect, sha

archive = producer / "share/wros/zig/zig-x86_64-linux-0.16.0.tar.xz"
prefix = "zig-x86_64-linux-0.16.0"
source_member = prefix + "/lib/std/math/gcd.zig"
if sha(archive) != "70e49664a74374b48b51e6f3fdfbf437f6395d42509050588bd49abe52ba3d00":
    raise ValueError("unexpected Zig archive")
with tarfile.open(archive, mode="r:xz") as source:
    data = source.extractfile(source_member).read()
if hashlib.sha256(data).hexdigest() != "0225995fbfcae25ee75b0243e3a6abcf5714a62c8b50b41f61437f0e9b7b455b":
    raise ValueError("unexpected upstream gcd implementation or tests")

group = cgroup_record()
output.mkdir(parents=True)
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
env = {k: v for k, v in os.environ.items() if not k.startswith(("WROS_", "UWVM_", "ZIG_"))}
env.update(PATH="/usr/bin:/bin", TMPDIR=str(output), LC_ALL="C")
result = dict(complete=False, cgroup=group, upstream="Zig 0.16.0", sdk_commit=revision,
              archive_sha256=sha(archive), test_sha256=hashlib.sha256(data).hexdigest(),
              vm_sha256=sha(vm), cases=[], rows=[])
receipt = output / "results.json"


def save():
    receipt.write_text(json.dumps(result, indent=2) + "\n")


def run(label, command, timeout=240):
    print(label, flush=True)
    log = output / (label + ".log")
    with log.open("xb") as out:
        process = subprocess.run(list(map(str, command)), cwd=output, env=env,
                                 stdout=out, stderr=subprocess.STDOUT, timeout=timeout)
    result["cases"].append(dict(name=label, exit=process.returncode, log_sha256=sha(log)))
    save()
    process.check_returncode()
    return log.read_text()


start = b"test gcd {\n    const expectEqual = std.testing.expectEqual;\n"
if data.count(start) != 1 or not data.endswith(b"}\n"):
    raise ValueError("unexpected original Zig test layout")
implementation, assertions = data.split(start)
if assertions.count(b"try expectEqual(") != 11:
    raise ValueError("unexpected number of upstream gcd assertions")
body = implementation + b'''
fn expectEqual(actual: anytype, expected: @TypeOf(actual)) error{Mismatch}!void {
    if (actual != expected) return error.Mismatch;
}
fn upstreamCases() error{Mismatch}!void {
''' + assertions + b'''
// Use Euclid's algorithm independently to verify dynamic unsigned cases.
fn reference(a: u64, b: u64) u64 {
    var x = a;
    var y = b;
    while (y != 0) {
        const next = x % y;
        x = y;
        y = next;
    }
    return x;
}

var seed: u64 = 0x76ad1d864419ce22;
fn random(state: *volatile u64) u64 {
    var x = state.*;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    state.* = x;
    return x;
}
export fn _start() void {
    upstreamCases() catch @trap();
    for (0..8192) |_| {
        const a = random(&seed);
        const b = random(&seed);
        if (gcd(a, b) != reference(a, b)) @trap();
    }
}
'''
app = output / "gcd-guest.zig"
app.write_bytes(body)
with tempfile.TemporaryDirectory(dir=output, prefix="host-zig-") as place:
    tmp = Path(place)
    with tarfile.open(archive, mode="r:xz") as source:
        source.extractall(tmp, filter="data")
    native = tmp / prefix
    env.update(ZIG_GLOBAL_CACHE_DIR=str(tmp / "gcache"), ZIG_LOCAL_CACHE_DIR=str(tmp / "lcache"))
    native_input = tmp / "gcd.zig"
    native_input.write_bytes(data)
    log = run("native-upstream", [native / "zig", "test", native_input,
                                 "--zig-lib-dir", native / "lib", "-O", "ReleaseSafe", "-fno-strip"])
    if "All 1 tests passed" not in log:
        raise ValueError("original Zig test suite did not execute")
    env.pop("ZIG_GLOBAL_CACHE_DIR")
    env.pop("ZIG_LOCAL_CACHE_DIR")

# A signed test site is independently verified by the SDK installer and frontend.
for bits, site in ((32, site32), (64, site64)):
    tag = f"wasm{bits}"
    installed = json.loads(run(f"{tag}-install", [sys.executable, "-I", "-B", sdk / "install/bootstrap.py",
        "install", "--local-repository", sdk, "--commit", revision, "--platform", "unitree", "--language", "zig",
        "--prefix", output / (tag + "-installed"), "--site-profile", site, "--", "--component", "development"]))
    artifact = output / (tag + ".wasm")
    frontend = Path(installed["directory"]) / "bin/wrzig"
    run(tag + "-wrzig", [frontend, app, "--target", tag, "-o", artifact, "--build-receipt"])
    build_file = output / (tag + ".wasm.wros-build.json")
    run(tag + "-verify", [frontend, "verify", "--artifact", artifact, "--receipt", build_file,
                          "--approved-receipt-sha256", sha(build_file), "--vm", vm])
    imports = inspect(artifact.read_bytes())
    if imports:
        raise ValueError("unexpected host imports")
    for engine in ("int", "aot"):
        run(tag + "-" + engine, [vm, *Profile(bits, mte=True, exceptions="noeh").uwvm_feature_flags(),
             "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
             "--runtime-memtag-mode", "sync", "--run", artifact])
    result["rows"].append(dict(target=tag, wasm_sha256=sha(artifact), imports=imports, assertions=11, generated=8192))
    save()
result["complete"] = True
save()
