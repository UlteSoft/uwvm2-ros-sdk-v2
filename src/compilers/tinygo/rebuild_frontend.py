"""Build the TinyGo host frontend and its Espressif LLVM dependencies offline."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def build(args):
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    goroot = args.goroot.resolve()
    if (goroot / "VERSION").read_text().splitlines()[0] != "go1.24.2":
        raise ValueError("the TinyGo frontend requires the pinned Go 1.24.2 bootstrap")
    pin = json.loads((ROOT / "upstream.json").read_bytes())["frontend_llvm"]
    project = (args.llvm_source or ROOT / "frontend/llvm-project").resolve()
    if args.llvm_source:
        revision = subprocess.check_output(["git", "-C", project, "rev-parse", "HEAD", "HEAD^{tree}"], text=True).splitlines()
        if revision != [pin["commit"], pin["tree"]]:
            raise ValueError("external LLVM source must be the pinned Espressif LLVM 19.1.2 revision")
    if not (project / "libunwind/include/mach-o/compact_unwind_encoding.h").is_file():
        raise ValueError("Espressif LLVM source lacks the compact-unwind header required by LLD")
    build_dir = (args.llvm_build or work / "llvm-build").resolve()
    build_dir.mkdir(parents=True, exist_ok=True)
    cache = build_dir / "CMakeCache.txt"
    if cache.is_file():
        homes = [line.split("=", 1)[1] for line in cache.read_text().splitlines()
                 if line.startswith("CMAKE_HOME_DIRECTORY:INTERNAL=")]
        if not homes or Path(homes[0]).resolve() != project / "llvm":
            raise ValueError("the existing LLVM build directory was configured with a different source tree")

    with tempfile.TemporaryDirectory(dir=work, prefix="frontend-") as temp:
        scratch = Path(temp)
        source = scratch / "tinygo"
        shutil.copytree(ROOT / "upstream", source)
        (source / "llvm-build").symlink_to(build_dir, target_is_directory=True)
        (source / "llvm-input").symlink_to(project, target_is_directory=True)
        go = goroot / "bin/go"
        env = dict(os.environ, TMPDIR=str(scratch), GOTMPDIR=str(scratch), GOROOT=str(goroot),
                   GOCACHE=str(scratch / "gocache"), GOPATH=str(scratch / "gopath"),
                   GOMODCACHE=str((args.modcache or scratch / "modcache").resolve()),
                   XDG_CACHE_HOME=str(scratch / "cache"), XDG_CONFIG_HOME=str(scratch / "config"),
                   GOOS="linux", GOARCH="amd64", GOAMD64="v1", CGO_ENABLED="1", GOENV="off", GOWORK="off",
                   GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off", SOURCE_DATE_EPOCH="0",
                   PATH=str(goroot / "bin") + os.pathsep + os.environ["PATH"])
        # LLVM and the cgo bindings may retain __FILE__ and DWARF source paths.
        # Go 1.24 supplies its own per-action map for go-build<nonce>/bNNN.
        # A later GCC map for all of scratch masks that narrower map in cgo.
        # Map only our source checkout, leaving sibling Go action paths to Go.
        maps = shlex.join([f"-ffile-prefix-map={project}=/src/espressif",
                           f"-ffile-prefix-map={build_dir}=/build/espressif",
                           f"-ffile-prefix-map={source}=/build/tinygo/tinygo"])
        for key in ("CFLAGS", "CXXFLAGS", "ASMFLAGS", "CGO_CPPFLAGS"):
            env[key] = (env.get(key, "") + " " + maps).strip()
        module_mode = "readonly" if args.modcache else "vendor"
        env["GOFLAGS"] = f"-trimpath -buildvcs=false -ldflags=-buildid= -mod={module_mode} -p={args.jobs}"
        if args.modcache:
            subprocess.run([go, "mod", "verify"], cwd=source, env=env, check=True)
        else:
            shutil.copytree(ROOT / "frontend/vendor", source / "vendor")

        # Configure using the permanent source path so interrupted Ninja builds can resume.
        # Upstream joins TINYGO_SOURCE_DIR and LLVM_PROJECTDIR after changing directory.
        options = ["-DLLVM_INCLUDE_TESTS=OFF", "-DLLVM_INCLUDE_DOCS=OFF", "-DLLVM_INCLUDE_EXAMPLES=OFF",
                   "-DLLVM_INCLUDE_BENCHMARKS=OFF", "-DLLVM_APPEND_VC_REV=OFF", "-DLLVM_CCACHE_BUILD=OFF",
                   "-DLLVM_FORCE_VC_REVISION=" + pin["commit"], "-DLLVM_FORCE_VC_REPOSITORY=" + pin["origin"]]
        make = ["make", "-f", "GNUmakefile", "-f", ROOT / "frontend.mk", "GO=" + shlex.quote(str(go)),
                "LLVM_BUILDDIR=llvm-build", "LLVM_PROJECTDIR=.", "TINYGO_SOURCE_DIR=" + shlex.quote(str(project)),
                "CLANG_SRC=llvm-input/clang", "LLD_SRC=llvm-input/lld", "LLVM_OPTION=" + " ".join(options),
                "SDK_JOBS=" + str(args.jobs)]
        subprocess.run([*make, "sdk-frontend-llvm"], cwd=source, env=env, check=True)
        version = subprocess.check_output([build_dir / "bin/llvm-config", "--version"], env=env, text=True).strip()
        if version != "19.1.2":
            raise ValueError(f"frontend expected LLVM 19.1.2, found {version}")
        subprocess.run([*make, "tinygo"], cwd=source, env=env, check=True)
        product = source / "build/tinygo"
        with product.open("rb") as executable:
            header = executable.read(20)
        if header[:6] != b"\x7fELF\x02\x01" or header[18:20] != b"\x3e\x00":
            raise ValueError("frontend build did not produce a native Linux x86-64 ELF")
        target = args.output.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".frontend-") as out:
            pending = Path(out) / "tinygo"
            shutil.copy2(product, pending)
            os.replace(pending, target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("work", "goroot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--modcache", type=Path, help="use a populated module cache, verified by Go against upstream/go.sum")
    parser.add_argument("--llvm-source", type=Path, help="use an external Git checkout at the pinned Espressif revision")
    parser.add_argument("--llvm-build", type=Path, help="build or resume LLVM dependencies here (default: WORK/llvm-build)")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    try:
        build(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
