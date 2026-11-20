"""@file upstream_zlib_archive.py
@brief Compile upstream zlib separately, archive with the SDK, and run its upstream test.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

sdk_repo, previous, zlib, site, vm, out = map(Path, sys.argv[1:])
sys.path[:0] = [str(sdk_repo / "tests"), str(sdk_repo / "install")]
from separate_compilation import cgroup_record
from guest_profile import Profile
from imports import inspect

group = cgroup_record()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
out.mkdir(mode=0o700)
report = {"complete": False, "cgroup": group, "steps": []}
baseline = json.loads((previous / "results.json").read_bytes())
assert baseline["sources"]["zlib"]["commit"] == "da607da739fa6047df13e66a2af6b8bec7c2a498"
assert baseline["cases"]["zlib-example"]["outcome"] == "passed"
assert subprocess.check_output(["git", "-C", zlib, "rev-parse", "HEAD"], text=True).strip() == baseline["sources"]["zlib"]["commit"]
assert not subprocess.check_output(["git", "-C", zlib, "status", "--porcelain"])
sdk = Path(json.loads((previous / "install.json").read_bytes())["directory"])
toolchain = Path(json.loads(site.read_bytes())["toolchain"])
env = {k: v for k, v in os.environ.items() if not k.startswith(("UWVM_", "WROS_", "XMAKE_"))}
env.update(PATH="/usr/bin:/bin", LC_ALL="C", TMPDIR=str(out))

def save():
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(label, command):
    proc = subprocess.run(list(map(str, command)), cwd=out, env=env, capture_output=True, timeout=180)
    (out / (label + ".log")).write_bytes(proc.stdout + proc.stderr)
    report["steps"].append({"case": label, "exit": proc.returncode})
    save()
    if proc.returncode:
        raise RuntimeError(label + " failed")

objects = []
base = [sdk / "bin/wrc", "-O3", "-g", "--eh", "-D", "Z_SOLO", "-I", zlib, "--build-receipt"]
for stem in ("adler32", "crc32", "deflate", "inffast", "inflate", "inftrees", "trees", "zutil"):
    obj = out / (stem + ".o")
    run("compile-" + stem, [*base, "-c", zlib / (stem + ".c"), "-o", obj])
    objects.append(obj)
library = out / "libz-wros.a"
run("archive", [sdk / "bin/wrar", "--toolchain", toolchain, "-o", library, *objects])
module = out / "zlib-test.wasm"
run("link-upstream-test", [*base, "--reactor", "--export", "_start", previous / "zlib-example/entry.c",
                           library, "-o", module])
assert not inspect(module.read_bytes())
assert json.loads(module.with_suffix(".wasm.wros-build.json").read_bytes())["mode"] == "strict"
for engine in ("int", "aot"):
    command = [vm, *Profile(32, "3.0", False, True, "eh").uwvm_feature_flags(), "--runtime-" + engine,
               "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
               "--runtime-memtag-mode", "sync", "--debug-fault-action", "exit", "--run", module]
    run(engine, command)
report.update(complete=True, upstream_commit=baseline["sources"]["zlib"]["commit"],
              sdk_commit=baseline["sdk_commit"], wasm_sha256=sha(module), archive_sha256=sha(library),
              object_sha256={p.name: sha(p) for p in objects})
save()
print("upstream zlib archive and both engines passed")
