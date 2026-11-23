"""Expose the authenticated WASIp1 headers and libraries at Clang's multiarch search paths."""
import os
from pathlib import Path

from compiler import digest

LAYOUT = "wasi-multiarch-v1"
TRIPLES = frozenset(f"wasm{bits}-wasip1{suffix}" for bits in (32, 64) for suffix in ("", "-threads"))


def directory(sdk, profile):
    version = sdk / "wasm-sysroots"
    if profile.wasm_version != "3.0":
        version /= "core" + profile.wasm_version
    name = "wasm-sysroot"
    if profile.exceptions == "noeh":
        name += "-noeh"
    if profile.mte:
        name += "-mtg"
    return version / name


def inputs(target):
    """Yield the build-receipt name, installed multiarch path and expected digest."""
    base = Path(target["sysroot"])
    for name, expected in target["files"].items():
        path = Path(name)
        if not path.is_relative_to(base):
            continue  # The resource dir, including compiler-rt builtins, is profile-specific.
        relative = path.relative_to(base)
        if relative == Path("include/c++/v1/__config_site"):
            relative = Path("include") / target["triple"] / "c++/v1/__config_site"
        yield name, relative, expected


def install(sdk, receipt, profile, target, *, source_root=None, verify_tree=False):
    """Link the verified profile into Clang's search paths under the SDK lock."""
    root = directory(sdk, profile)
    source_root = source_root or receipt.parent
    pending = []
    for name, relative, expected in inputs(target):
        source = source_root / name
        dest = root / relative
        if (".." in relative.parts or dest.resolve() != dest or source.resolve() != source
                or not source.is_file()):
            raise ValueError("symlink in installed sysroot: " + str(dest))
        if dest.exists():
            if not dest.is_file() or not dest.samefile(source) and digest(dest) != expected:
                raise ValueError("multiarch sysroot collision: " + str(dest))
        else:
            pending.append((source, dest))
    linked = []
    try:
        for source, dest in pending:
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, dest)
            linked.append(dest)
        if verify_tree:
            verify(root, profile, target)
    except BaseException:
        for dest in reversed(linked):
            dest.unlink()
        raise


def verify(root, profile, target):
    """Check exactly the files searchable by the selected triple, including common headers."""
    if root.resolve() != root or not root.is_dir():
        raise ValueError("missing or redirected multiarch sysroot: " + str(root))
    remaining = {relative: sha for _, relative, sha in inputs(target)}
    for parent, directories, files in os.walk(root):
        directory = Path(parent)
        for name in directories:
            if (directory / name).is_symlink():
                raise ValueError("symlink in multiarch sysroot: " + str(directory / name))
        if directory in (root / "include", root / "lib"):
            directories[:] = [d for d in directories if d == profile.triple or d not in TRIPLES]
        for name in files:
            path = directory / name
            relative = path.relative_to(root)
            expected = remaining.pop(relative, None)
            if expected is None or path.is_symlink() or not path.is_file() or digest(path) != expected:
                raise ValueError("unexpected multiarch sysroot input: " + str(path))
    if remaining:
        raise ValueError("incomplete multiarch sysroot: " + str(next(iter(remaining))))
