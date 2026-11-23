"""Materialize the commit-pinned Wasm sysroot alongside the installed native Linux tools."""
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile

if __name__ == "__main__":
    # The installer launches this policy with Python's isolated (-I) mode.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from compiler import digest
from guest_profile import Profile

DIRECTORY = Path("share/toolchains/portable")
SYSROOTS = DIRECTORY / "sysroots"
RECEIPT = "sysroots.json"
PUBLIC_HEADERS = Path("include/sysroot")
RESOURCE_ARCHIVE = "clang-resource-headers.tar.xz"
MAX_BYTES = 128 * 1024 * 1024


def native_host():
    """Read the Python userspace ELF ABI, including the ARM calling convention."""
    if sys.platform != "linux":
        raise ValueError("the native SDK compiler requires Linux")
    with Path(sys.executable).open("rb") as stream:
        header = stream.read(52)
    if len(header) == 52 and header[:4] == b"\x7fELF" and header[5:7] == b"\x01\x01":
        identity = (header[4], int.from_bytes(header[18:20], "little"))
        if identity == (1, 40):
            flags = int.from_bytes(header[36:40], "little")
            if flags >> 24 == 5 and flags & 0x600 != 0x600:
                return "linux-armhf" if flags & 0x400 else "linux-arm"
        else:
            host = {(2, 62): "linux-x86_64", (1, 3): "linux-i686", (2, 183): "linux-aarch64"}.get(identity)
            if host:
                return host
    raise ValueError("unsupported Linux userspace ELF ABI: " + sys.executable)


def library_entries(target):
    """Map the verified sysroot paths to the guest archives and CRT files published for linkers."""
    profile = target_profile(target)
    guest_lib = PurePosixPath(target["sysroot"]) / "lib" / profile.triple
    builtin = PurePosixPath(target["resource"]) / "lib" / profile.triple.replace("-wasip1", "-unknown-wasip1") / "libclang_rt.builtins.a"
    result = {}
    for name in target["files"]:
        path = PurePosixPath(name)
        if path == builtin or (path.parent == guest_lib and path.suffix in (".a", ".o")):
            result[name] = Path(profile.flavor) / path.name
    if len(set(result.values())) != len(result):
        raise ValueError("the target contains colliding public library names")
    return result


def header_entries(target):
    """Map original sysroot header names to regular files in the public SDK."""
    profile = target_profile(target)
    include = PurePosixPath(target["sysroot"]) / "include"
    c = PUBLIC_HEADERS / "c"
    cpp = PUBLIC_HEADERS / "c++"
    result = {}
    for name in target["files"]:
        path = PurePosixPath(name)
        if not path.is_relative_to(include):
            continue
        parts = path.relative_to(include).parts
        if (not parts or path.parts[:1] != ("output",) or ".." in path.parts
                or path.as_posix() != name):
            raise ValueError("invalid sysroot header path: " + name)
        if parts[0] == profile.triple:
            relative = Path(*parts[1:])
            base = c
            if relative == Path("wasi/version.h"):
                base /= "config/mte" if profile.mte else "config/nomte"
        elif parts[:2] == ("c++", "v1"):
            relative = Path(*parts[2:])
            base = cpp
            if relative == Path("__config_site"):
                base /= "config/threads" if profile.threads else "config/single"
        else:
            # Herbceptions lives at the include root next to the libunwind headers.
            relative = Path(*parts)
            base = cpp if parts[0] == "herbceptions" else c
        if not relative.parts:
            raise ValueError("missing sysroot header name: " + name)
        result[name] = base / relative
    if len(set(result.values())) != len(result):
        raise ValueError("the target contains colliding public header names")
    return result


def verify_public_headers(sdk, receipt, target):
    """Bind the expanded, digest-checked input to its reviewable public file."""
    for name, relative in header_entries(target).items():
        source = sdk / relative
        expanded = receipt.parent / name
        if (source.resolve() != source or not source.is_file()
                or not source.samefile(expanded) and digest(source) != target["files"][name]):
            raise ValueError("public sysroot header differs: " + str(relative))


def target_profile(target):
    fields = target["guest_profile"]
    profile = Profile(**{key: fields[key] for key in Profile.__dataclass_fields__})
    if (fields != profile.to_dict() or target["triple"] != profile.triple
            or target["profile"] != profile.exceptions or target["threads"] is not profile.threads):
        raise ValueError("inconsistent profile in sysroot receipt")
    return profile


def library_key(profile):
    # Existing default packages have their receipt and headers at the triple root.
    if profile.flavor == "core3.0-eh-mte":
        return profile.triple
    return profile.triple + "/" + profile.flavor


def package_directory(sdk, key):
    """Locate the compiler resource package and producer receipt for one profile."""
    triple, _, flavor = key.partition("/")
    return sdk / SYSROOTS / triple / (flavor or "core3.0-eh-mte")


def available(sdk):
    return (sdk / DIRECTORY / "distribution.json").is_file()


def libraries(manifest):
    """Read the original package, the per-triple catalog or the per-profile catalog."""
    if manifest.get("format") == "wros-native-cc-v1":
        entries = {manifest["library"]: {k: manifest[k] for k in ("archive", "archive_sha256", "sysroots_sha256")}}
    elif manifest.get("format") in ("wros-native-cc-v2", "wros-native-cc-v3", "wros-native-cc-v4"):
        entries = manifest["libraries"]
    else:
        raise ValueError("unrecognized portable compiler distribution")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("empty portable library catalog")
    key_pattern = r"wasm(?:32|64)-wasip1(?:-threads)?"
    if manifest["format"] in ("wros-native-cc-v3", "wros-native-cc-v4"):
        key_pattern += r"(?:/core[123]\.0-(?:noeh|eh)-(?:nomte|mte))?"
    for key, entry in entries.items():
        if not re.fullmatch(key_pattern, key):
            raise ValueError("invalid sysroot catalog key " + key)
        fields = {"archive", "archive_sha256", "sysroots_sha256"}
        if "public_headers" in entry:
            if (manifest["format"] != "wros-native-cc-v4" or entry["public_headers"] != PUBLIC_HEADERS.as_posix()
                    or entry["archive"] != RESOURCE_ARCHIVE):
                raise ValueError("invalid public header layout for " + key)
            fields.add("public_headers")
        if (set(entry) != fields
                or not re.fullmatch(r"[A-Za-z0-9._-]+\.tar\.xz", entry["archive"])
                or not all(re.fullmatch("[0-9a-f]{64}", entry[k]) for k in ("archive_sha256", "sysroots_sha256"))):
            raise ValueError("invalid portable sysroot entry for " + key)
    return entries


def published_pair(toolchain, receipt, profile, compiler_sha256, producer_sha256):
    """Authenticate a host rebuild's pairing with the immutable guest build receipt."""
    sdk = Path(__file__).resolve().parents[1]
    if toolchain != sdk / DIRECTORY:
        return False
    manifest = json.loads((toolchain / "distribution.json").read_bytes())
    key = library_key(profile) if manifest["format"] in ("wros-native-cc-v3", "wros-native-cc-v4") else profile.triple
    entry = libraries(manifest).get(key)
    location = package_directory(sdk, key) if manifest["format"] == "wros-native-cc-v4" else sdk / "lib" / key
    return (manifest["host"] == native_host() and manifest["programs"]["clang"] == compiler_sha256
            and entry is not None and receipt == location / RECEIPT
            and producer_sha256 is not None and manifest.get("sysroot_producer_sha256") == producer_sha256
            and digest(receipt) == entry["sysroots_sha256"])


def prepare(sdk, verify=False, language="cpp", triple="wasm32-wasip1", *, profile=None):
    # A target rebuild publishes under this same directory lock. Each reader sees
    # matching receipts, headers and archives while it assembles its compiler paths.
    lock = os.open(sdk, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX if verify else fcntl.LOCK_SH)
        return _prepare(sdk, verify, language, triple, profile, lock)
    finally:
        os.close(lock)


def _prepare(sdk, verify, language, triple, profile, lock):
    import sysroot_layout
    root = sdk / DIRECTORY
    manifest = json.loads((root / "distribution.json").read_bytes())
    host = native_host()
    if manifest["host"] != host:
        raise ValueError(f"installed compiler is for {manifest['host']}, running userspace is {host}")
    entries = libraries(manifest)
    key = triple
    if profile is not None:
        key = library_key(profile) if manifest["format"] in ("wros-native-cc-v3", "wros-native-cc-v4") else profile.triple
    if key not in entries:
        raise ValueError("no bundled sysroot for " + key + "; installed entries: " + ", ".join(sorted(entries)))
    triple = key.partition("/")[0]
    triple_root = sdk / "lib" / triple
    library = package_directory(sdk, key) if manifest["format"] == "wros-native-cc-v4" else sdk / "lib" / key
    entry = entries[key]
    if triple_root.resolve() != triple_root or library.resolve() != library:
        raise ValueError("invalid bundled sysroot location")
    receipt = library / RECEIPT
    if receipt.is_symlink() or digest(receipt) != entry["sysroots_sha256"]:
        raise ValueError("installed sysroot receipt digest differs")
    target, = json.loads(receipt.read_bytes())["targets"]
    actual = target_profile(target)
    if (actual.triple != triple or (profile is not None and actual != profile)
            or (manifest["format"] in ("wros-native-cc-v3", "wros-native-cc-v4") and library_key(actual) != key)):
        raise ValueError("bundled sysroot does not match " + (profile.identity if profile else key))
    programs = ["clang", "wasm-ld", "llvm-ar"]
    if language == "cpp":
        programs.append("clang++")
    for name in programs:
        path = root / "bin" / name
        if path.is_symlink() or digest(path) != manifest["programs"][name] or not os.access(path, os.X_OK):
            raise ValueError("installed native executable differs: " + name)
    destination = library / "output"
    if destination.is_symlink():
        raise ValueError("refusing a symlink for the SDK sysroot")
    multiarch = manifest.get("sysroot_layout") == sysroot_layout.LAYOUT
    if not verify:
        search_tree = sysroot_layout.directory(sdk, actual) / "include" / triple
        if destination.is_dir() and (not multiarch or (search_tree / "stdio.h").is_file()):
            return root, receipt
        # Other readers can compile concurrently. Re-read the catalog under the
        # writer lock before expanding a missing profile or repairing an older layout.
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _prepare(sdk, True, language, key, profile, lock)
    roles = target["files"]
    loose_headers = "public_headers" in entry
    if destination.is_dir():
        present = {}
        for file in destination.rglob("*"):
            if file.is_symlink():
                raise ValueError("unexpected symlink in the installed sysroot")
            if file.is_file():
                present[file.relative_to(library).as_posix()] = digest(file)
        if present != roles:
            raise ValueError("installed sysroot differs from its pinned inventory")
        if loose_headers:
            verify_public_headers(sdk, receipt, target)
        if multiarch:
            sysroot_layout.install(sdk, receipt, actual, target, verify_tree=True)
        return root, receipt
    archive = library / entry["archive"]
    if archive.parent != library:
        raise ValueError("invalid bundled sysroot archive name")
    if archive.is_symlink() or digest(archive) != entry["archive_sha256"]:
        raise ValueError("installed sysroot archive digest differs")
    public = {name: Path("lib") / triple / relative for name, relative in library_entries(target).items()}
    if loose_headers:
        public.update(header_entries(target))
    resource_include = PurePosixPath(target["resource"]) / "include"
    with tempfile.TemporaryDirectory(dir=library) as temp:
        scratch = Path(temp)
        seen, total = set(), 0
        for name, relative in public.items():
            source = sdk / relative
            if source.resolve() != source or not source.is_file() or digest(source) != roles[name]:
                raise ValueError("public sysroot input differs: " + str(relative))
            member = PurePosixPath(name)
            if member.parts[:1] != ("output",) or ".." in member.parts or member.as_posix() != name:
                raise ValueError("invalid public sysroot input path")
            destination_file = scratch / member
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, destination_file)
            seen.add(name)
        with tarfile.open(archive, "r|xz") as stream:
            for member in stream:
                relative = PurePosixPath(member.name)
                if (not member.isreg() or member.name not in roles or member.name in seen or
                        relative.is_absolute() or relative.as_posix() != member.name or
                        relative.parts[:1] != ("output",) or ".." in relative.parts or
                        loose_headers and not relative.is_relative_to(resource_include)):
                    raise ValueError("unexpected member in the SDK sysroot")
                total += member.size
                if member.size < 0 or total > MAX_BYTES:
                    raise ValueError("SDK sysroot exceeds extraction budget")
                out = scratch / relative
                out.parent.mkdir(parents=True, exist_ok=True)
                with stream.extractfile(member) as source, out.open("xb") as writer:
                    shutil.copyfileobj(source, writer)
                if digest(out) != roles[member.name]:
                    raise ValueError("bad SDK sysroot member digest: " + member.name)
                out.chmod(0o644)
                seen.add(member.name)
        if seen != roles.keys():
            raise ValueError("incomplete SDK sysroot")
        if multiarch:
            sysroot_layout.install(sdk, receipt, actual, target, source_root=scratch, verify_tree=True)
        (scratch / "output").rename(destination)
    return root, receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--target", help="prepare one installed catalog entry (default: all)")
    parser.add_argument("--language", choices=("c", "cpp"), required=True)
    args = parser.parse_args()
    sdk = args.sdk.resolve()
    manifest = json.loads((sdk / DIRECTORY / "distribution.json").read_bytes())
    for triple in ([args.target] if args.target else libraries(manifest)):
        prepare(sdk, verify=True, language=args.language, triple=triple)
