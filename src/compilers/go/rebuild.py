"""Materialize the Go guest toolchain in a fresh SDK prefix or package its native products."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from host_package import unpack, sha


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(work, goroot):
    env = dict(os.environ)
    env.update(GOROOT=str(goroot), GOOS="linux", GOARCH="amd64", GOAMD64="v1", CGO_ENABLED="0",
               GOENV="off", GOWORK="off", GOFLAGS="", GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off",
               GOCACHE=str(work / "gocache"), GOMODCACHE=str(work / "modcache"), TMPDIR=str(work),
               GOTMPDIR=str(work), XDG_CACHE_HOME=str(work / "cache"), SOURCE_DATE_EPOCH="0",
               PATH=str(goroot / "bin") + os.pathsep + env.get("PATH", ""))
    return env


def command(args, env, cwd):
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def stage_host(source, prefix, role, work, *, without_tinygo_binary=False):
    dest = prefix / "libexec" / role
    unpack(role, dest, work, cache=os.environ.get("WROS_DIST_CACHE", work / "downloads"), without_tinygo_binary=without_tinygo_binary)
    return dest


def apply_runtime(source, role, dest):
    producer = source / "src/compilers" / role
    lock = json.loads((producer / "upstream.json").read_bytes())
    for name, expected in lock["local_files"].items():
        src = producer / "upstream" / name
        if sha(src) != expected:
            raise ValueError("producer overlay does not match its source manifest: " + name)
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)


def llvm_backend(source, prefix):
    backend = prefix / "share/toolchains/tinygo-llvm"
    backend.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / "bin/packages/linux-x86_64/manifest.json").read_bytes()) if not all(
        (backend / n).is_file() for n in ("clang", "wasm-ld")) else None
    for name in ("clang", "wasm-ld"):
        if not (backend / name).is_file():
            records = manifest["packages"]
            row = next(entry for entry in records.values() if entry["member"] == name)
            reader = load(source / "install/install.py", "sdk_native_archive")
            reader.unpack_executable(source / row["path"], row, backend / name)
    if not (backend / "runtime").is_dir():
        shutil.copytree(source / "src/compilers/tinygo/runtime", backend / "runtime")
    return backend


def llvm_config_from_source(source, work, env, jobs):
    project = source / "src/compilers/cc/llvm-project"
    build = work / "llvm"
    command(["cmake", "-S", project / "llvm", "-B", build, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
             "-DLLVM_TARGETS_TO_BUILD=WebAssembly", "-DLLVM_INCLUDE_TESTS=OFF", "-DLLVM_INCLUDE_EXAMPLES=OFF",
             "-DLLVM_INCLUDE_BENCHMARKS=OFF", "-DLLVM_INCLUDE_DOCS=OFF", "-DLLVM_ENABLE_ZLIB=OFF", "-DLLVM_ENABLE_ZSTD=OFF",
             "-DLLVM_ENABLE_LIBXML2=OFF", "-DLLVM_ENABLE_TERMINFO=OFF", "-DLLVM_ENABLE_LIBEDIT=OFF"], env, work)
    command(["cmake", "--build", build, "--parallel", str(jobs), "--target", "llvm-config", "LLVMIRReader", "LLVMBitWriter"], env, work)
    return str(build / "bin/llvm-config")


def build_pass(config, cxx, source, destination, env, work):
    config = shutil.which(config) if config else None
    if not config:
        raise ValueError("set WROS_LLVM_CONFIG or --llvm-config to the LLVM 23.1.5 development build's llvm-config")
    version = subprocess.check_output([config, "--version"], text=True, env=env).strip()
    if version.split("-")[0] != "23.1.5":
        raise ValueError("TinyGo prepare-ir requires the bundled backend's LLVM 23.1.5 headers and libraries")
    flags = shlex.split(subprocess.check_output([config, "--cxxflags", "--ldflags", "--link-static", "--libs",
                          "irreader", "bitwriter", "core", "--system-libs"], text=True, env=env))
    command([cxx, "-O2", "-g0", "-Wl,--build-id=none", "-ffile-prefix-map=" + str(source.parent) + "=/src",
             source, *flags, "-o", destination], env, work)


def materialize(opts):
    src = opts.source.resolve()
    prefix = opts.prefix.resolve()
    base = opts.work.resolve()
    prefix.mkdir(parents=True, exist_ok=True)
    base.mkdir(parents=True, exist_ok=True)
    language = opts.language
    name = "wrgo" if language == "go" else "wrtg"
    tools = {}
    # The public installer builds under its own fresh staging prefix. A failed
    # build never exposes a partial selection at the final destination.
    with tempfile.TemporaryDirectory(prefix=language + "-", dir=base) as d:
        work = Path(d)
        goroot = stage_host(src, prefix, "go", work)
        env = environment(work, goroot)
        env["GOFLAGS"] = "-p=" + str(opts.jobs)
        go = goroot / "bin/go"
        (prefix / "bin").mkdir(exist_ok=True)
        tools[name] = prefix / "bin" / name
        if opts.mode == "source":
            # The published host launchers use the pinned Go runtime. Build them
            # before the guest overlay changes the runtime linked into Linux executables.
            command([go, "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid= -X main.language=" + language,
                     "-o", tools[name], "."], env, src / "src/compilers/go/command")
        if language == "go":
            apply_runtime(src, "go", goroot)
            for product in ("asm", "compile", "link"):
                target = goroot / "pkg/tool/linux_amd64" / product
                if opts.mode == "source":
                    built = work / product
                    command([go, "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", built, "cmd/" + product], env, work)
                    os.replace(built, target)
                else:
                    os.replace(prefix / "share/toolchains/go" / product, target)
                tools[product] = target
        else:
            from_source = opts.mode == "source"
            published_frontend = prefix / "share/toolchains/tinygo-llvm/frontend"
            tiny = stage_host(src, prefix, "tinygo", work,
                              without_tinygo_binary=from_source or published_frontend.is_file())
            if not from_source and published_frontend.is_file():
                (tiny / "bin").mkdir(exist_ok=True)
                os.replace(published_frontend, tiny / "bin/tinygo")
            apply_runtime(src, "tinygo", tiny)
            backend = llvm_backend(src, prefix)
            tools["prepare-ir"] = backend / "prepare-ir"
            if from_source:
                config = opts.llvm_config or llvm_config_from_source(src, work, env, opts.jobs)
                build_pass(config, opts.cxx, src / "src/compilers/tinygo/prepare_ir.cpp",
                           tools["prepare-ir"], env, work)
                producer = src / "src/compilers/tinygo"
                shutil.copytree(producer / "upstream/src/runtime", tiny / "src/runtime", dirs_exist_ok=True)
                command([sys.executable, "-I", "-B", producer / "rebuild_frontend.py", "--goroot", goroot,
                         "--work", work / "frontend-build", "--jobs", opts.jobs, "--output", tiny / "bin/tinygo"], env, work)
                tools["frontend"] = tiny / "bin/tinygo"
        if any(not file.is_file() or not os.access(file, os.X_OK) for file in tools.values()):
            raise ValueError("selection misses a native executable")
        if opts.package_dir:
            packer = load(src / "src/compilers/package_native.py", "sdk_pack")
            destination = opts.package_dir.resolve()
            destination.mkdir(parents=True, exist_ok=True)
            records = {}
            with tempfile.TemporaryDirectory(dir=destination, prefix=".publish-") as path:
                staging = Path(path)
                for key, file in tools.items():
                    archive = staging / (key + ".tar.xz")
                    record = packer.package(file, key, archive)
                    name = key + "-" + record["compressed_sha256"][:20] + ".tar.xz"
                    record["path"] = "bin/packages/linux-x86_64/wrgo/" + language + "/" + name
                    records[language + "-" + key] = record
                    os.replace(archive, destination / name)
                pending = staging / "native.json"
                pending.write_text(json.dumps(records, sort_keys=True, indent=2) + "\n")
                os.replace(pending, destination / "native.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE.parents[2])
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--mode", choices=("binary", "source"), required=True)
    parser.add_argument("--language", choices=("go", "tinygo"), required=True)
    parser.add_argument("--llvm-config", default=os.environ.get("WROS_LLVM_CONFIG"))
    parser.add_argument("--cxx", default=os.environ.get("CXX", "c++"))
    parser.add_argument("--package-dir", type=Path, help="write deterministic native archives and manifest entries")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    try:
        materialize(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        parser.exit(1, f"{parser.prog}: {e}\n")
