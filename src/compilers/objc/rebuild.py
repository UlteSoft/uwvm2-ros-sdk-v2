"""Build an offline Objective-C or Objective-C++ SDK with its own Clang and GNUstep guest runtime."""
import argparse
import errno
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "cc"
RUNTIME = HERE.parents[1] / "runtimes/objc"
sys.path[:0] = [str(HERE / "driver"), str(CC / "policy")]
from compiler import compiler_environment, digest, make_command
from portable_cc import DIRECTORY, libraries, prepare, target_profile
from runtime import ARCHIVES, PUBLIC_INCLUDE, header_hashes, objc_flags, receipt, receipt_path, runtime_lock, runtime_root


def link_or_copy(source, destination):
    try:
        os.link(source, destination)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
        shutil.copy2(source, destination)
    return destination


def install_core_file(source, destination):
    # Installed metadata may share an inode with the immutable source or installer cache.
    destination = Path(destination)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        replacement = link_or_copy(source, Path(temporary) / destination.name)
        os.replace(replacement, destination)
    return destination


def verify_compiler_sources():
    """Verify the GNUstep port integrated in the common LLVM source tree."""
    record = json.loads((HERE / "upstream.json").read_bytes())
    for entry in [*record["changes"], *record["sdk_overlays"]]:
        if digest(CC / "llvm-project" / entry["path"]) != entry["integrated_sha256"]:
            raise ValueError("GNUstep compiler source differs from its recorded revision: " + entry["path"])


def install_headers(sdk, sources):
    """Publish one complete public include tree and compare it with every profile's build."""
    include = sdk / PUBLIC_INCLUDE / "objc"
    if include.resolve() != include.absolute():
        raise ValueError("redirected GNUstep include directory: " + str(include))
    include.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=include.parent) as temporary:
        staged = Path(temporary) / "objc"
        staged.mkdir()
        for source in sources:
            shutil.copy2(source, staged / source.name)
        expected = header_hashes(staged)
        try:
            staged.rename(include)
        except OSError:
            # A nonempty directory cannot be replaced by rename. Identical builders share it.
            if not include.is_dir() or include.is_symlink():
                raise
            actual = header_hashes(include)
            differences = sorted(name for name in actual.keys() | expected.keys()
                                 if actual.get(name) != expected.get(name))
            if differences:
                raise ValueError("conflicting GNUstep public headers: " + ", ".join(differences))


def publish_runtime(sdk, profile, compiler, staged):
    library = runtime_root(sdk, profile)
    marker = receipt_path(sdk, profile)
    if library.resolve() != library.absolute() or marker.parent.resolve() != marker.parent.absolute():
        raise ValueError("redirected GNUstep installation directory")
    library.mkdir(parents=True, exist_ok=True)
    marker.parent.mkdir(parents=True, exist_ok=True)
    record = receipt(sdk, profile, compiler, archive_dir=staged)
    if (record["compiler_source_sha256"] != digest(HERE / "upstream.json")
            or record["runtime_source_sha256"] != digest(RUNTIME / "upstream.json")):
        raise ValueError("installed GNUstep source records differ from the sources used for this build")
    (staged / "runtime.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    with runtime_lock(sdk, profile, exclusive=True):
        for name in ARCHIVES:
            os.replace(staged / name, library / name)
        os.replace(staged / "runtime.json", marker)


def build_runtime(sdk, work, profile, jobs, cmake):
    tools, sysroot = prepare(sdk, language="cpp", profile=profile)
    cc, selected = make_command(tools, [sysroot], profile, "c", ["-c"], verify=True)
    cxx, _ = make_command(tools, [sysroot], profile, "cpp", ["-c"])
    work.mkdir(parents=True, exist_ok=True)
    env = compiler_environment(tools)
    # Ninja cannot track the contents of a compiler replaced at the same path.
    build = work / "gnu-runtime" / selected["compiler_sha256"] / selected["closure_sha256"]
    source = RUNTIME / "libobjc2"
    configs = {
        "CMAKE_SYSTEM_NAME": "Generic", "CMAKE_SYSTEM_PROCESSOR": "wasm" + str(profile.address_bits),
        "CMAKE_TRY_COMPILE_TARGET_TYPE": "STATIC_LIBRARY", "CMAKE_BUILD_TYPE": "Release",
        "CMAKE_AR": tools / "bin/llvm-ar", "CMAKE_RANLIB": work / "llvm-ranlib",
        "WASM": "ON", "OLDABI_COMPAT": "OFF", "TESTS": "OFF",
        "WASM_EXCEPTIONS": "ON" if profile.exceptions == "eh" else "OFF",
        "FETCHCONTENT_FULLY_DISCONNECTED": "ON", "FETCHCONTENT_SOURCE_DIR_ROBINMAP": RUNTIME / "robin-map",
        "CMAKE_DISABLE_FIND_PACKAGE_tsl-robin-map": "ON",
    }
    for kind, command in [("C", cc), ("CXX", cxx), ("ASM", cc), ("OBJC", cc), ("OBJCXX", cxx)]:
        args = [*command[1:-1], "-ffunction-sections", "-fdata-sections"]
        if kind in {"OBJC", "OBJCXX"}:
            args.extend(objc_flags(profile))
        configs["CMAKE_" + kind + "_COMPILER"] = command[0]
        configs["CMAKE_" + kind + "_FLAGS"] = shlex.join(args)
    # CMake and Ninja are host build programs. The target compiler and libraries use explicit SDK paths.
    build_env = dict(os.environ, LC_ALL="C", TZ="UTC")
    # llvm-ranlib is llvm-ar's alternate invocation name. Refresh it when reusing this work area.
    install_core_file(tools / "bin/llvm-ar", work / "llvm-ranlib")
    subprocess.run([cmake, "-S", source, "-B", build, "-G", "Ninja",
                    *[f"-D{k}={v}" for k, v in configs.items()]], env=build_env, check=True)
    subprocess.run([cmake, "--build", build, "--target", "objc-static", "--parallel", str(jobs)],
                   env=build_env, check=True)
    install_headers(sdk, [*sorted((source / "objc").glob("*.h")), build / "objc/objc-config.h"])
    objects = []
    includes = [sdk / PUBLIC_INCLUDE, sdk / "include/u2rosv2/universal/objc", sdk / "include/u2rosv2/universal/c"]
    for unit in sorted((RUNTIME / "bindings").glob("*.m")):
        obj = work / (unit.stem + ".o")
        subprocess.run([*cc, *objc_flags(profile), "-O3", "-ffunction-sections", "-fdata-sections",
                        *["-I" + str(directory) for directory in includes], unit, "-o", obj],
                       check=True, env=env)
        objects.append(obj)
    # Start each binding archive empty. Stage outside lib on the SDK filesystem.
    with tempfile.TemporaryDirectory(dir=sdk) as temporary:
        archives = Path(temporary)
        shutil.copyfile(build / "libobjc.a", archives / "libobjc.a")
        subprocess.run([tools / "bin/llvm-ar", "rcsD", archives / "libuwrosobjc.a", *objects], env=env, check=True)
        publish_runtime(sdk, profile, selected, archives)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    producer = parser.add_mutually_exclusive_group(required=True)
    producer.add_argument("--bootstrap", type=Path, help="build the native LLVM compiler and complete C/C++ sysroot")
    producer.add_argument("--installed-compiler", action="store_true",
                          help="build guest runtimes with the native compiler and catalog already in the prefix")
    parser.add_argument("--platform", choices=["generic"], default="generic")
    parser.add_argument("--language", choices=["objc", "objcpp"], required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--cmake", default="cmake")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    sdk, work = args.prefix.resolve(), args.work.resolve()
    if work.is_relative_to(CC) or work.is_relative_to(HERE) or sdk.is_relative_to(work):
        parser.error("keep the build area separate from the source and installed SDK")
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / "tmp"
    scratch.mkdir(exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), PYTHONDONTWRITEBYTECODE="1", LC_ALL="C", TZ="UTC")
    verify_compiler_sources()
    for item in json.loads((RUNTIME / "upstream.json").read_bytes())["changes"]:
        if digest(RUNTIME / item["path"]) != item["sha256"]:
            raise ValueError("modified libobjc2 source: " + item["path"])
    if args.bootstrap:
        core = work / "core-sdk"
        subprocess.run([sys.executable, "-I", "-B", CC / "rebuild.py", "--language", "cpp",
                        "--prefix", core, "--work", work / "core-build", "--bootstrap", args.bootstrap.resolve(),
                        "--matrix", "--jobs", str(args.jobs), "--cmake", args.cmake], check=True)
        for name in ("share", "include", "lib"):
            if (core / name).is_dir():
                shutil.copytree(core / name, sdk / name, copy_function=install_core_file, dirs_exist_ok=True)
    catalog = json.loads((sdk / DIRECTORY / "distribution.json").read_bytes())
    for key in libraries(catalog):
        _, manifest = prepare(sdk, verify=True, language="cpp", triple=key)
        target, = json.loads(manifest.read_bytes())["targets"]
        profile = target_profile(target)
        build_runtime(sdk, work / profile.identity, profile, args.jobs, args.cmake)
    (sdk / "bin").mkdir(exist_ok=True)
    command = "wrocxx" if args.language == "objcpp" else "wroc"
    frontend = sdk / "bin" / command
    compiler = sdk / DIRECTORY / "bin/clang"
    try:
        link_or_copy(compiler, frontend)
    except FileExistsError:
        if not frontend.samefile(compiler) and digest(frontend) != digest(compiler):
            raise ValueError("conflicting native Objective-C frontend: " + str(frontend))


if __name__ == "__main__":
    main()
