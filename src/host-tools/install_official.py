"""Install Xmake and build the native VM from their pinned official GitHub projects."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(SDK / "src/compilers"))
from official_dist import fetch_archive

VM_DIRECTORIES = ("src", "third-parties", "xmake", "tools/dependencies")


def command(argv, cwd, env):
    subprocess.run(argv, cwd=cwd, env=env, check=True, stdout=sys.stderr)


def native_xmake(origin, host, work, downloads, env, jobs):
    if host == "linux-x86_64":
        release = origin["linux_x86_64"]
        return fetch_archive(release["url"], release["sha256"], downloads)
    release = origin["source"]
    archive = fetch_archive(release["url"], release["sha256"], downloads)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(work, filter="data")
    source = work / ("xmake-" + origin["version"])
    build = work / "xmake-build"
    bootstrap = work / "bootstrap"
    command(["sh", "configure", "--prefix=" + str(bootstrap)], source, env)
    command(["make", "-j", str(jobs)], source, env)
    command(["make", "install", "PREFIX=" + str(bootstrap), "DESTDIR="], source, env)
    xmake = bootstrap / "bin/xmake"
    command([xmake, "f", "-c", "-y", "-p", "linux", "-m", "release", "-o", build, "--embed=y"], source / "core", env)
    command([xmake, "build", "-j", str(jobs), "cli"], source / "core", env)
    return build / "xmake"


def native_vm(origin, host, work, xmake, env, jobs):
    source = work / "vm"
    source.mkdir()
    command(["git", "init", "-q"], source, env)
    command(["git", "remote", "add", "origin", origin["repository"] + ".git"], source, env)
    command(["git", "config", "remote.origin.promisor", "true"], source, env)
    command(["git", "config", "remote.origin.partialclonefilter", "blob:none"], source, env)
    command(["git", "fetch", "--depth=1", "--no-tags", "--filter=blob:none", "origin", origin["commit"]], source, env)
    revision = subprocess.check_output(["git", "rev-parse", "FETCH_HEAD", "FETCH_HEAD^{tree}"], cwd=source, env=env, text=True)
    if revision.splitlines() != [origin["commit"], origin["tree"]]:
        raise ValueError("the official VM checkout differs from its pinned commit or tree")
    command(["git", "sparse-checkout", "set", "--cone", *VM_DIRECTORIES], source, env)
    command(["git", "checkout", "--detach", origin["commit"]], source, env)
    build = work / "vm-build"
    arch = host.removeprefix("linux-")
    command([xmake, "f", "-y", "-p", "linux", "-a", arch, "-m", "release", "-o", build,
             "--use-llvm-compiler=y", "--use-cxx-module=n", "--execution-int=uwvm-int",
             "--execution-jit=llvm", "--import-u2rosv2=y", "--llvm-runtimes-provider=bundled",
             "--openssl-provider=bundled", "--llvm-build-jobs=" + str(jobs), "--openssl-build-jobs=" + str(jobs)], source, env)
    command([xmake, "build", "-j", str(jobs), "uwvm2-ros"], source, env)
    return build / "linux" / arch / "release/uwvm2-ros"


def install(host, cache, work, jobs):
    installer = runpy.run_path(str(SDK / "install/install.py"))
    env = dict(os.environ, TMPDIR=str(work), TEMP=str(work), TMP=str(work), XMAKE_TMPDIR=str(work),
               XMAKE_GLOBALDIR=str(work / "global"), XMAKE_CONFIGDIR=str(work / "config"),
               GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    env.pop("XMAKE_PROGRAM_DIR", None)
    env.pop("UWVM_ROS_QUALIFIED_PREBUILT_LLVM", None)
    downloads = cache / "sha256"
    bindir = SDK / "bin"
    bindir.mkdir(exist_ok=True)
    receipts = {}
    for tool in ("xmake", "uwvm2-ros"):
        origin = json.loads((HERE / tool / "UPSTREAM.json").read_bytes())
        # A recipe change also invalidates binaries compiled under a previous SDK.
        recipe = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        bucket = cache / "host-tools" / host / tool / origin["commit"] / recipe
        bucket.mkdir(parents=True, exist_ok=True)
        program = bucket / tool
        receipt = bucket / "receipt.json"
        with (bucket / "build.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            spec = {"repository": origin["repository"], "commit": origin["commit"], "host": host}
            if tool == "uwvm2-ros":
                spec["tree"] = origin["tree"]
            if receipt.exists():
                saved = json.loads(receipt.read_bytes())
                if any(saved.get(k) != v for k, v in spec.items()) or saved["sha256"] != installer["digest"](program):
                    raise ValueError("official host tool cache failed verification: " + tool)
            else:
                with tempfile.TemporaryDirectory(dir=work, prefix=tool + "-") as tmp:
                    stage = Path(tmp)
                    if tool == "xmake":
                        built = native_xmake(origin, host, stage, downloads, env, jobs)
                    else:
                        built = native_vm(origin, host, stage, bindir / "xmake", env, jobs)
                    installer["require_host"](built, host)
                    shutil.copyfile(built, bucket / "new-program")
                    (bucket / "new-program").chmod(0o755)
                    os.replace(bucket / "new-program", program)
                    saved = dict(spec, sha256=installer["digest"](program))
                    pending = receipt.with_suffix(".new")
                    pending.write_text(json.dumps(saved, indent=2) + "\n")
                    os.replace(pending, receipt)
            installer["require_host"](program, host)
            shutil.copy2(program, bindir / tool)
            receipts[tool] = saved
    dest = SDK / "share/host-tools"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "origins.json").write_text(json.dumps(receipts, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--jobs", required=True, type=int)
    args = parser.parse_args()
    install(args.host, args.cache, args.work, args.jobs)
