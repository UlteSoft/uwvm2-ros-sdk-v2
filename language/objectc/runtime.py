"""Shared identity and source checks for the single-threaded GNUstep Wasm runtime."""
import json
from pathlib import Path
import shutil
import tarfile

from compiler import digest

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "third-parties/objectc"
ARCHIVES = {"libobjc2-a21ae931.tar.gz": "b5e34d8c8066765be58dbc95b4328b363a6bb5146ae860a96ed9f022826198c7",
            "robin-map-1.4.0.tar.gz": "7930dbf9634acfc02686d87f615c0f4f33135948130b8922331c16d90a03250c"}
PATCHES = ("objc-CGObjCGNU.cpp.patch", "objc-Clang.cpp.patch")
FRONTEND_REVISION = "392dfff97d29b59d77e5cac6d4b6ef2585fe7117"
FLAGS = ["-fobjc-runtime=gnustep-2.0", "-fno-objc-exceptions", "-fno-objc-arc"]

def frontend_record(binary):
    return {"format": "wros-objective-c-compiler", "compiler_sha256": digest(binary),
            "llvm_revision": FRONTEND_REVISION, "targets": ["wasm32", "wasm64"],
            "patches": {name: digest(VENDOR / name) for name in PATCHES}}

def frontend(toolchain, explicit=None):
    binary = (explicit if explicit is not None else toolchain / "bin/wros-objc-clang").absolute()
    marker = binary.with_name(binary.name + ".json")
    if not binary.is_file() or not marker.is_file() or marker.stat().st_size > 2048:
        raise ValueError("build the Wasm-only Objective-C frontend with language/objectc/build_frontend.py")
    if json.loads(marker.read_bytes()) != frontend_record(binary):
        raise ValueError("the Objective-C compiler differs from its recorded build")
    return binary

def vendor_inputs():
    names = [*ARCHIVES, "libobjc2-wasm.patch", *PATCHES]
    values = {name: digest(VENDOR / name) for name in names}
    if any(values[name] != expected for name, expected in ARCHIVES.items()):
        raise ValueError("Objective-C vendor archive differs from the pinned upstream release")
    return values

def extract(name, destination):
    destination.mkdir()
    with tarfile.open(VENDOR / name, "r:gz") as archive:
        for member in archive:
            if member.isdir(): continue
            parts = Path(member.name).parts
            if (not member.isfile() or len(parts) < 2 or Path(member.name).is_absolute() or ".." in parts):
                raise ValueError("unexpected path or entry type in " + name)
            target = destination.joinpath(*parts[1:])
            target.parent.mkdir(exist_ok=True, parents=True)
            with archive.extractfile(member) as stream, target.open("xb") as out:
                shutil.copyfileobj(stream, out)

def abi(profile, compiler, base_record):
    return {"format": "wros-gnustep-runtime", "profile": profile.to_dict(),
            "producer_sha256": base_record["compiler_sha256"], "sysroot_sha256": base_record["closure_sha256"],
            "objc_compiler_sha256": digest(compiler), "vendor": vendor_inputs()}

def public_files(root):
    include = root / "include"
    objc = include / "objc"
    library = root / "libobjc.a"
    if library.is_symlink() or not library.is_file():
        raise ValueError("GNUstep archive must be a regular file")
    if include.is_symlink() or objc.is_symlink() or not objc.is_dir() or set(include.iterdir()) != {objc}:
        raise ValueError("unexpected GNUstep include layout")
    headers = sorted(objc.iterdir())
    if any(path.is_symlink() or not path.is_file() or path.suffix != ".h" for path in headers):
        raise ValueError("unexpected GNUstep header entry")
    if not {objc / "runtime.h", objc / "objc-config.h"} <= set(headers):
        raise ValueError("incomplete GNUstep headers")
    return {p.relative_to(root).as_posix(): digest(p) for p in [library, *headers]}

def verify_runtime(root, profile, compiler, base_record):
    marker = root / "runtime.json"
    if not marker.is_file() or marker.stat().st_size > 16384:
        raise ValueError("prepare the matching language runtime with language/objectc/build_runtime.py")
    expected = abi(profile, compiler, base_record)
    expected["files"] = public_files(root)
    if json.loads(marker.read_bytes()) != expected:
        raise ValueError("Objective-C runtime, headers, compiler or sysroot differs from its build receipt")
    return marker


def verified_inputs(toolchain, profile, base_record, compiler=None, directory=None):
    clang = frontend(toolchain, compiler)
    root = (directory or toolchain / "share/wros/objectc" / profile.identity).resolve(strict=True)
    marker = verify_runtime(root, profile, clang, base_record)
    return {"objc_frontend": clang, "objc_runtime": marker, "objc_archive": root / "libobjc.a"}
