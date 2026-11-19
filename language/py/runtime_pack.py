"""@file runtime_pack.py
@brief Publish and consume digest-bound CPython target libraries for exact compiler and libc profiles.
"""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

from build_interpreter import LANG, ROOT, SHA256
from compiler import digest

DIST = ROOT / "third-parties/cpython-runtime"
FORMAT = "wros-cpython-runtime"


def identity(profile, build_info):
    """@brief Bind one runtime to the official source, SDK adaptations, compiler and exact libc closure."""
    inputs = ("build_interpreter.py", "freeze_encodings.py", "runtime_paths.mk", "runtime_pack.py")
    return dict(format=FORMAT, source_sha256=SHA256, compiler_sha256=build_info["compiler_sha256"],
                closure_sha256=build_info["closure_sha256"], profile=profile.to_dict(),
                recipe={name: digest(LANG / name) for name in inputs})


def publish(source, target, destination, expected):
    """@brief Export target-only headers, frozen encodings and the Wasm static interpreter to a new release file."""
    headers = source / "Include"
    files = {"include/" + f.relative_to(headers).as_posix(): f for f in headers.rglob("*.h") if f.is_file()}
    files.update({"include/pyconfig.h": target / "pyconfig.h", "include/frozen.h": target / "frozen.h",
                  "lib/libpython3.14.a": target / "libpython3.14.a"})
    with destination.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:xz", preset=4) as archive:
        for name, path in sorted(files.items()):
            data = path.read_bytes()
            item = tarfile.TarInfo(name)
            item.size, item.mode = len(data), 0o644
            archive.addfile(item, io.BytesIO(data))
    receipt = {**expected, "file": destination.name, "sha256": digest(destination),
               "archive_sha256": digest(target / "libpython3.14.a")}
    Path(str(destination) + ".json").write_text(json.dumps(receipt, indent=2) + "\n")


def restore(work, profile, expected):
    """@brief Restore only the prebuilt pack indexed by this SDK for the exact reviewed build inputs."""
    index = DIST / (profile.identity + ".json")
    if not index.exists():
        return None
    receipt = json.loads(index.read_bytes())
    if any(receipt.get(k) != v for k, v in expected.items()):
        return None
    name = profile.identity + ".tar.xz"
    if receipt.get("file") != name:
        raise ValueError("unexpected CPython runtime release filename")
    with (DIST / name).open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != receipt["sha256"]:
            raise ValueError("CPython runtime pack digest differs from installed release")
        stream.seek(0)
        seen, total = set(), 0
        with tarfile.open(fileobj=stream, mode="r:xz") as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                header = path.parts[:1] == ("include",) and path.suffix == ".h"
                if (not member.isreg() or path.as_posix() != member.name or ".." in path.parts or
                        member.name in seen or not (header or member.name == "lib/libpython3.14.a")):
                    raise ValueError("unexpected CPython runtime member")
                total += member.size
                if total > 256 * 1024 * 1024 or len(seen) >= 4096:
                    raise ValueError("oversized CPython runtime pack")
                seen.add(member.name)
                archive.extract(member, work, filter="data")
    library = work / "lib/libpython3.14.a"
    if not {"lib/libpython3.14.a", "include/Python.h", "include/pyconfig.h", "include/frozen.h"} <= seen or digest(library) != receipt["archive_sha256"]:
        raise ValueError("incomplete CPython runtime pack")
    return work / "include", work / "include", library
