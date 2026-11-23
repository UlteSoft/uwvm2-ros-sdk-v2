"""Build the SDK's WebAssembly Clang, LLD, archiver and WASIp1 C/C++ sysroot offline."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "policy")]
from compiler import confined, digest
from guest_profile import Profile
from portable_cc import (DIRECTORY, PUBLIC_HEADERS, RECEIPT, RESOURCE_ARCHIVE, header_entries,
                         libraries, library_entries, library_key, native_host, package_directory, target_profile)


def checked(command, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    print(" ".join(map(str, command[:7])), flush=True)
    with log.open("a") as stream:
        stream.write(json.dumps(list(map(str, command))) + "\n")
        stream.flush()
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)


def source_id():
    checksum = hashlib.sha256()
    for tree in (HERE / "llvm-project", HERE / "wasi-libc"):
        for folder, dirs, names in os.walk(tree):
            dirs.sort()
            for name in sorted(names):
                file = Path(folder) / name
                checksum.update(os.fsencode(file.relative_to(HERE)) + b"\0")
                checksum.update(bytes.fromhex(digest(file)))
    return checksum.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def host_tools(args, build, *, cross=None):
    src = HERE / "llvm-project"
    flag = "-Os -g0 -DNDEBUG"
    flag += " -ffile-prefix-map=" + str(src) + "=/usr/src/llvm-23.1.5"
    flag += " -ffile-prefix-map=" + str(build) + "=/usr/src/llvm-build"
    bootstrap = args.bootstrap / "bin"
    for name in ("clang", "clang++", "ld.lld"):
        if not (bootstrap / name).is_file():
            raise ValueError("missing native LLVM bootstrap executable " + str(bootstrap / name))
    options = {
        "CMAKE_BUILD_TYPE": "Release", "CMAKE_C_COMPILER": bootstrap / "clang",
        "CMAKE_CXX_COMPILER": bootstrap / "clang++", "CMAKE_SKIP_RPATH": "ON",
        "CMAKE_EXE_LINKER_FLAGS": "-fuse-ld=" + str(bootstrap / "ld.lld") + " -Wl,-s",
        "CMAKE_SHARED_LINKER_FLAGS": "-fuse-ld=" + str(bootstrap / "ld.lld"),
        "CMAKE_C_FLAGS_RELEASE": flag, "CMAKE_CXX_FLAGS_RELEASE": flag,
        "LLVM_ENABLE_PROJECTS": "clang;lld", "LLVM_TARGETS_TO_BUILD": "WebAssembly",
        "LLVM_DEFAULT_TARGET_TRIPLE": "wasm32-wasip1", "LLVM_ENABLE_ASSERTIONS": "ON",
        "LLVM_ENABLE_PLUGINS": "OFF", "LLVM_EXPORT_SYMBOLS_FOR_PLUGINS": "OFF",
        "LLVM_INCLUDE_TESTS": "OFF", "LLVM_INCLUDE_EXAMPLES": "OFF", "LLVM_INCLUDE_BENCHMARKS": "OFF",
        "LLVM_INCLUDE_DOCS": "OFF", "CLANG_INCLUDE_DOCS": "OFF", "CLANG_ENABLE_CIR": "OFF",
        "CLANG_PLUGIN_SUPPORT": "OFF", "LLVM_ENABLE_ZLIB": "OFF", "LLVM_ENABLE_ZSTD": "OFF",
        "LLVM_ENABLE_LIBXML2": "OFF", "LLVM_ENABLE_LIBEDIT": "OFF", "LLVM_ENABLE_TERMINFO": "OFF",
        "LLVM_ENABLE_BINDINGS": "OFF", "LLVM_APPEND_VC_REV": "OFF", "LLVM_PARALLEL_LINK_JOBS": "1",
        "LLVM_RELATIVE_PATHS_IN_FILES": "ON", "Python3_EXECUTABLE": sys.executable,
        "WROS_NATIVE_DRIVER": "ON",
    }
    targets = ["clang", "lld", "llvm-ar"]
    if cross is None:
        targets.extend(["clang-resource-headers", "llvm-ranlib", "llvm-nm", "llvm-config"])
        if native_host() == "linux-arm":
            # LLVMSupport's C11 atomics may require the GNU runtime on ARMv5.
            options["CMAKE_CXX_STANDARD_LIBRARIES"] = "-Wl,--push-state,-Bstatic,-latomic,--pop-state"
    else:
        options.update(cross)
    log = build.parent / "host.log"
    checked([args.cmake, "-G", "Ninja", "-S", src / "llvm", "-B", build,
             *[f"-D{k}={v}" for k, v in options.items()]], log)
    checked([args.cmake, "--build", build, "--parallel", str(args.jobs), "--target", *targets], log)
    # Some LLVM generator versions materialize driver aliases only via their targets.
    for name, original in (("clang++", "clang"), ("wasm-ld", "lld")):
        link = build / "bin" / name
        if not link.exists():
            link.symlink_to(original)


def package_sysroot(staging, receipt, data, target):
    profile = target_profile(target)
    key = library_key(profile)
    triple_root = staging / "lib" / profile.triple
    library = package_directory(staging, key)
    library.mkdir(parents=True, exist_ok=True)
    archive = library / RESOURCE_ARCHIVE
    public = library_entries(target)
    headers = header_entries(target)
    resource_headers = Path(target["resource"]) / "include"
    names = {path.name: target["files"][relative] for relative, path in public.items()}
    required = {"crt1.o", "crt1-command.o", "crt1-reactor.o", "libc.a", "libc-printscan-long-double.a",
                "libc++.a", "libc++abi.a", "libclang_rt.builtins.a", "libherbceptions.a"}
    herb = target.get("herbceptions", {})
    bridge = herb.get("legacy_exception_bridge", {})
    eh = profile.exceptions == "eh"
    if (not required <= names.keys() or eh != ("libunwind.a" in names)
            or target["builtins_sha256"] != names["libclang_rt.builtins.a"]
            or herb.get("archive") != "lib/" + profile.triple + "/libherbceptions.a"
            or herb.get("archive_sha256") != names["libherbceptions.a"]
            or bridge.get("enabled") is not eh or bridge.get("sha256") != names["libc++abi.a"]
            or data["mte"] is not profile.mte or data["wasm_version"] != profile.wasm_version
            or target["feature_flags"] != profile.llvm_feature_flags()
            or not data.get("producer_mte_codegen", {}).get(str(profile.address_bits))):
        raise ValueError("incomplete or inconsistent C/C++ runtime for " + profile.identity)
    with tarfile.open(archive, "w:xz", format=tarfile.PAX_FORMAT, preset=4) as output:
        for relative, expected in sorted(target["files"].items()):
            source = confined(receipt.parent, relative)
            if (not relative.startswith("output/") or source != receipt.parent / relative
                    or digest(source) != expected):
                raise ValueError("sysroot build changed before packaging " + relative)
            if relative in public:
                dest = triple_root / public[relative]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
                continue
            if relative in headers:
                dest = staging / headers[relative]
                if dest.exists():
                    if digest(dest) != expected:
                        raise ValueError("profiles disagree on public header: " + str(headers[relative]))
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, dest)
                continue
            if not Path(relative).is_relative_to(resource_headers):
                raise ValueError("unclassified sysroot input: " + relative)
            item = tarfile.TarInfo(relative)
            item.size = source.stat().st_size
            item.mode = 0o644
            with source.open("rb") as stream:
                output.addfile(item, stream)
    packaged = dict(data, targets=[target])
    packaged.pop("commands", None)
    if len(data["targets"]) > 1:
        packaged["input_receipt_sha256"] = digest(receipt)
    write_json(library / RECEIPT, packaged)
    return key, {"archive": archive.name, "archive_sha256": digest(archive),
                 "sysroots_sha256": digest(library / RECEIPT), "public_headers": PUBLIC_HEADERS.as_posix()}


def release_tools(toolchain):
    """Check the packaged compiler, linker, archiver and resource headers before using them as build inputs."""
    from herbceptions_sysroot import TOOLS
    release = json.loads((HERE / "distribution/distribution.json").read_bytes())
    host = native_host()
    if host != release["host"]:
        release = json.loads((HERE.parents[2] / "bin/packages" / host / "wrcc/cc-distribution.json").read_bytes())
        if host != release["host"]:
            raise ValueError("published C/C++ distribution host differs from the running userspace")
    for name in TOOLS:
        executable = toolchain / "bin" / name
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError("missing target build tool: " + str(executable))
        published = "llvm-ar" if name == "llvm-ranlib" else name
        if published in release["programs"] and digest(executable) != release["programs"][published]:
            raise ValueError("supplied tool differs from the published executable: " + name)
    receipt = package_directory(HERE.parents[2], "wasm32-wasip1") / "sysroots.json"
    if digest(receipt) != libraries(release)["wasm32-wasip1"]["sysroots_sha256"]:
        raise ValueError("invalid reference receipt for the published Clang resource headers")
    reference, = json.loads(receipt.read_bytes())["targets"]
    prefix = reference["resource"] + "/include/"
    expected = {name[len(prefix):]: sha for name, sha in reference["files"].items() if name.startswith(prefix)}
    resource = Path(subprocess.check_output([toolchain / "bin/clang", "-print-resource-dir"], text=True).strip())
    headers = resource / "include"
    actual = {path.relative_to(headers).as_posix(): digest(path) for path in headers.rglob("*") if path.is_file()}
    if not expected or actual != expected:
        raise ValueError("bootstrap Clang resource headers differ from the published header inventory")
    return release


def published_header_hashes(prefix, entries, packed):
    """Recover shared header pins, including the unbuilt profiles of a release overlay."""
    retained, replaced = {}, {}
    for key, entry in entries.items():
        if "public_headers" not in entry:
            continue
        record = package_directory(prefix, key) / RECEIPT
        if not record.exists():
            # A target-only package can carry the rest of the source release's catalog.
            record = package_directory(HERE.parents[2], key) / RECEIPT
        if not record.is_file() or record.resolve() != record or digest(record) != entry["sysroots_sha256"]:
            raise ValueError("missing or changed published sysroot receipt for " + key)
        target, = json.loads(record.read_bytes())["targets"]
        if library_key(target_profile(target)) != key:
            raise ValueError("wrong profile in published sysroot receipt for " + key)
        pins = replaced if key in packed else retained
        for name, path in header_entries(target).items():
            expected = target["files"][name]
            if pins.setdefault(path, expected) != expected:
                raise ValueError("published profiles disagree on public header: " + str(path))
    return retained, replaced


def install_package_files(staging, prefix, obsolete, retained, replaced):
    """Preflight every shared input and publish the catalog last under the caller's lock."""
    catalog = DIRECTORY / "distribution.json"
    files = sorted(path.relative_to(staging) for path in staging.rglob("*") if path.is_file())
    files.remove(catalog)
    changes = []
    for relative in [*files, *obsolete, catalog]:
        dest = prefix / relative
        if dest.resolve() != dest or dest.exists() and not dest.is_file():
            raise ValueError("invalid package destination: " + str(dest))
        source = staging / relative
        if relative in obsolete:
            if digest(dest) != obsolete[relative]:
                raise ValueError("cannot retire changed sysroot archive: " + str(dest))
        else:
            actual = digest(source)
            if retained.get(relative, actual) != actual:
                raise ValueError("retained profile needs a different public header: " + str(relative))
            if dest.exists():
                previous = digest(dest)
                if previous == actual:
                    continue  # Preserve hardlinks held by expanded SDKs and the installer cache.
                if relative.is_relative_to(PUBLIC_HEADERS) and replaced.get(relative) != previous:
                    raise ValueError("conflicting public sysroot header: " + str(dest))
        changes.append(relative)
    backups = staging / "previous"
    applied = []
    try:
        for relative in changes:
            dest = prefix / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                backup = backups / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.link(dest, backup)
            if relative in obsolete:
                dest.unlink()
            else:
                os.replace(staging / relative, dest)
            applied.append(relative)
    except BaseException:
        for relative in reversed(applied):
            backup = backups / relative
            if backup.exists():
                os.replace(backup, prefix / relative)
            else:
                (prefix / relative).unlink()
        raise


def publish(prefix, language, tools, receipts, provenance, release):
    prefix.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=prefix) as temporary:
        staging = Path(temporary)
        bundle = staging / DIRECTORY
        bundle.mkdir(parents=True)
        if release is None:
            (bundle / "bin").mkdir()
            (staging / "bin").mkdir()
            programs = ["clang", "wasm-ld", "llvm-ar"] + (["clang++"] if language == "cpp" else [])
            hashes = {}
            for name in programs:
                path = bundle / "bin" / name
                if name == "clang++":
                    os.link(bundle / "bin/clang", path)
                else:
                    shutil.copyfile(tools / "bin" / name, path)
                    path.chmod(0o755)
                hashes[name] = digest(path)
            os.link(bundle / "bin/clang", staging / "bin" / ("wrcc" if language == "cpp" else "wrc"))
            entries = {}
        else:
            hashes = release["programs"]
            entries = dict(libraries(release))
        packed = {}
        for receipt in receipts:
            receipt = receipt.resolve(strict=True)
            data = json.loads(receipt.read_bytes())
            if (data.get("schema") != "uwvm-memtag-sysroot-build-v1" or data.get("status") != "built-awaiting-qualification"
                    or data.get("producer") != "herbceptions" or data.get("herbceptions_runtime") is not True
                    or data.get("compiler_sha256") != hashes["clang"] or not data.get("sources") or not data.get("targets")):
                raise ValueError("receipt does not describe a completed C/C++ sysroot from the selected compiler: " + str(receipt))
            for target in data["targets"]:
                if library_key(target_profile(target)) in packed:
                    raise ValueError("duplicate profile in supplied sysroot receipts: " + target["triple"])
                key, entry = package_sysroot(staging, receipt, data, target)
                packed[key] = entry
        catalog = {
            "format": "wros-native-cc-v4", "host": native_host(), "programs": hashes, "libraries": entries,
            "sysroot_layout": "wasi-multiarch-v1",
            "llvm_revision": provenance["upstreams"]["llvm"]["commit"],
            "herbceptions_revision": provenance["upstreams"]["herbceptions"]["commit"],
        }
        if release and "sysroot_producer_sha256" in release:
            catalog["sysroot_producer_sha256"] = release["sysroot_producer_sha256"]
        # Multiple target-only jobs can finish in the same release prefix. Merge under the
        # directory lock, and expose the new catalog after its complete payload is in place.
        lock = os.open(prefix, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            dist = prefix / DIRECTORY / "distribution.json"
            if dist.exists():
                previous = json.loads(dist.read_bytes())
                installed = libraries(previous)
                # A source-mode install initially contains just the source release's
                # reference catalog. It has no installed libraries to inherit.
                if release or any((package_directory(prefix, key) / RECEIPT).exists() for key in installed):
                    if (previous["format"] != catalog["format"] or any(previous.get(name) != catalog.get(name)
                            for name in ("programs", "host", "llvm_revision", "herbceptions_revision",
                                         "sysroot_producer_sha256"))):
                        raise ValueError("the existing package prefix belongs to another toolchain")
                    entries.update(installed)
            retained, replaced = published_header_hashes(prefix, entries, packed)
            obsolete = {}
            for key, entry in packed.items():
                library = package_directory(prefix, key)
                prior = entries.get(key)
                if (library / "output").exists() and prior != entry:
                    raise ValueError("package into a fresh prefix before replacing an expanded sysroot: " + key)
                if prior and prior["archive"] != entry["archive"]:
                    old_archive = library / prior["archive"]
                    if old_archive.exists():
                        obsolete[old_archive.relative_to(prefix)] = prior["archive_sha256"]
            entries.update(packed)
            write_json(bundle / "distribution.json", catalog)
            install_package_files(staging, prefix, obsolete, retained, replaced)
        finally:
            os.close(lock)


def build_profiles(args):
    matrix = args.matrix or args.list_profiles
    targets = args.target or (["wasm32", "wasm64"] if matrix and args.core == "3.0" else ["wasm32"])

    def choices(value, default):
        if value is not None:
            return (value,)
        return (default, not default) if matrix else (default,)

    result = []
    for target in dict.fromkeys(targets):
        bits = int(target[4:])
        for threads in choices(args.threads, False):
            if threads and args.core == "1.0":
                if args.threads:
                    raise ValueError("WASIp1 threads require Core 2.0 or later")
                continue
            for eh in choices(args.eh, args.core == "3.0"):
                if eh and args.core != "3.0" and args.eh is None:
                    continue
                for mte in choices(args.mte, True):
                    result.append(Profile(bits, args.core, threads, mte, "eh" if eh else "noeh"))
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    producer = cli.add_mutually_exclusive_group()
    producer.add_argument("--bootstrap", type=Path, help="native LLVM prefix used to build WROS Clang from source")
    producer.add_argument("--toolchain", type=Path,
                          help="build only guest libraries with the published clang/LLD/ar, resource headers and LLVM helpers")
    cli.add_argument("--target", action="append", choices=("wasm32", "wasm64"),
                     help="guest pointer ABI (repeat for both, default: wasm32)")
    cli.add_argument("--matrix", action="store_true",
                     help="build each supported ABI, thread model, EH and MTE setting at the selected Core version; axis options narrow the matrix")
    cli.add_argument("--list-profiles", action="store_true", help="print the matching buildable profiles as JSON")
    cli.add_argument("--pack-receipt", action="append", type=Path,
                     help="package a completed build from --toolchain without rebuilding (repeat for multiple receipts)")
    cli.add_argument("--work", type=Path)
    cli.add_argument("--prefix", type=Path)
    cli.add_argument("--language", choices=("c", "cpp"))
    cli.add_argument("--jobs", type=int, default=4)
    cli.add_argument("--cmake", default="cmake")
    cli.add_argument("--core", choices=("1.0", "2.0", "3.0"), default="3.0")
    cli.add_argument("--threads", action=argparse.BooleanOptionalAction)
    cli.add_argument("--eh", action=argparse.BooleanOptionalAction)
    cli.add_argument("--mte", action=argparse.BooleanOptionalAction)
    args = cli.parse_args()
    try:
        profiles = build_profiles(args)
    except ValueError as error:
        cli.error(str(error))
    if args.list_profiles:
        print(json.dumps([profile.to_dict() for profile in profiles], indent=2))
        return
    if not (args.bootstrap or args.toolchain) or not (args.prefix and args.language):
        cli.error("select --bootstrap or --toolchain and specify --prefix and --language")
    if args.pack_receipt:
        if (not args.toolchain or args.matrix or args.target or args.core != "3.0"
                or any(value is not None for value in (args.threads, args.eh, args.mte))):
            cli.error("--pack-receipt uses --toolchain and the exact profiles recorded in each input")
    elif not args.work:
        cli.error("building from source requires --work")
    native_host()
    if args.jobs < 1:
        cli.error("--jobs must be positive")
    args.prefix = args.prefix.resolve()
    provenance = json.loads((HERE / "UPSTREAM.json").read_bytes())
    if args.pack_receipt:
        compiler = args.toolchain.resolve(strict=True)
        publish(args.prefix, args.language, compiler, args.pack_receipt, provenance, release_tools(compiler))
        return
    args.work = args.work.resolve()
    if HERE.is_relative_to(args.work) or args.work.is_relative_to(HERE):
        cli.error("choose a build directory outside the compiler source tree")
    tmp = args.work / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(tmp), SOURCE_DATE_EPOCH="1793664000", ZERO_AR_DATE="1", LC_ALL="C", TZ="UTC")
    from build_sysroot import build
    identity = source_id()
    if args.toolchain:
        compiler = args.toolchain.resolve(strict=True)
        release = release_tools(compiler)
    else:
        args.bootstrap = args.bootstrap.resolve(strict=True)
        compiler = args.work / "host" / identity
        host_tools(args, compiler)
        release = None
    receipts = []
    for prof in profiles:
        directory = args.work / "sysroot" / identity / prof.identity
        receipts.append(build(args, compiler, directory, identity, provenance, prof))
    publish(args.prefix, args.language, compiler, receipts, provenance, release)


if __name__ == "__main__":
    main()
