"""Guest ABI and receipt shared by the source builder and native compiler policy."""
from contextlib import contextmanager
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path

from compiler import digest

PUBLIC_INCLUDE = Path("include/sysroot")
ARCHIVES = ("libobjc.a", "libuwrosobjc.a")
FORMAT = "uwros-gnustep-guest-v2"


def objc_flags(profile):
    return ("-fobjc-runtime=gnustep-2.0", "-fno-objc-arc",
            "-fobjc-exceptions" if profile.exceptions == "eh" else "-fno-objc-exceptions",
            "-Xclang", "-fobjc-dispatch-method=legacy")


def runtime_root(sdk, profile):
    return sdk / "lib" / profile.triple / profile.flavor


def receipt_path(sdk, profile):
    return sdk / "share/uwros/objc" / profile.triple / profile.flavor / "runtime.json"


def checked_file(path):
    if path.resolve() != path.absolute() or not path.is_file():
        raise ValueError("missing or redirected GNUstep input: " + str(path))
    return path


def header_hashes(objc):
    if objc.resolve() != objc.absolute() or not objc.is_dir():
        raise ValueError("invalid GNUstep public include directory: " + str(objc))
    files = {}
    for path in sorted(objc.iterdir()):
        if path.suffix != ".h":
            raise ValueError("unexpected GNUstep include entry: " + str(path))
        files[path.name] = digest(checked_file(path))
    if not {"objc-config.h", "runtime.h"} <= files.keys():
        raise ValueError("incomplete GNUstep public headers")
    return files


def inventory(sdk, profile, archive_dir=None):
    library = runtime_root(sdk, profile)
    files = {(PUBLIC_INCLUDE / "objc" / name).as_posix(): sha
             for name, sha in header_hashes(sdk / PUBLIC_INCLUDE / "objc").items()}
    for name in ARCHIVES:
        source = (archive_dir or library) / name
        files[(library / name).relative_to(sdk).as_posix()] = digest(checked_file(source))
    return files


def receipt(sdk, profile, compiler, *, producer_sha256=None, archive_dir=None):
    return {
        "format": FORMAT,
        "profile": profile.to_dict(),
        "compiler_sha256": producer_sha256 or compiler["compiler_sha256"],
        "sysroot_sha256": compiler["closure_sha256"],
        "compiler_source_sha256": digest(sdk / "src/compilers/objc/upstream.json"),
        "runtime_source_sha256": digest(sdk / "src/runtimes/objc/upstream.json"),
        "files": inventory(sdk, profile, archive_dir),
    }


@contextmanager
def runtime_lock(sdk, profile, *, exclusive=False):
    directory = receipt_path(sdk, profile).parent
    if directory.resolve() != directory.absolute():
        raise ValueError("redirected GNUstep receipt directory: " + str(directory))
    lock = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        os.close(lock)


def verified_runtime(sdk, profile, compiler):
    contents = checked_file(receipt_path(sdk, profile)).read_bytes()
    # A cross-built host consumes the same guest archives as the native WASIp1 producer.
    # make_command has already authenticated this pairing against the host catalog.
    if json.loads(contents) != receipt(sdk, profile, compiler, producer_sha256=compiler["sysroot_producer_sha256"]):
        raise ValueError("GNUstep runtime or its toolchain differs from the guest build receipt")
    return runtime_root(sdk, profile), sha256(contents).hexdigest()
