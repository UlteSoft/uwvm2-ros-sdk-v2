"""Import pinned upstream build sources into a new directory for SDK maintenance."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile


HERE = Path(__file__).resolve().parent
VM_PATHS = ["LICENSE.md", "README.md", "src", "xmake", "xmake.lua", "third-parties", "tools/dependencies"]
VM_LIST_SHA256 = "74e5998d9698d2ce7923c782248e339ddb35f457313372aab50f8a15848d9d2d"
OPENSSL = PurePosixPath("third-parties/openssl")
OPENSSL_INPUT = OPENSSL / "upstream"
OPENSSL_DIRS = {"Configurations", "crypto", "ssl", "providers", "include", "engines", "exporters",
                "util", "external", "os-dep", "tools"}
OPENSSL_FILES = {"ACKNOWLEDGEMENTS.md", "AUTHORS.md", "LICENSE.txt", "README.md", "INSTALL.md", "VERSION.dat",
                 "Configure", "config", "configdata.pm.in", "build.info"}
OPENSSL_FULL_HASH = "ecf889968127e9cac6cda5fe572beb69e2a3e20e276ab7bb4a1e730b1b72b30b"


def put(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(mode)


def xmake_product(path):
    if any(part in {".git", ".gitignore", ".gitattributes", ".github", ".circleci"} for part in path.parts):
        return False
    if path.is_relative_to("core/src/lz4/lz4"):
        child = path.relative_to("core/src/lz4/lz4").parts[0]
        return child in {"lib", "LICENSE"}
    return True


def import_xmake(archive, output):
    origin = json.loads((HERE / "xmake/UPSTREAM.json").read_bytes())
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != origin["source"]["sha256"]:
            raise ValueError("incorrect Xmake release source archive")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:gz") as packed:
            for member in packed:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts or path.parts[0] != "xmake-" + origin["version"]:
                    raise ValueError("invalid Xmake source archive path")
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError("unexpected Xmake source archive member")
                relative = PurePosixPath(*path.parts[1:])
                if xmake_product(relative):
                    with packed.extractfile(member) as file:
                        put(output / relative, file.read(), 0o755 if member.mode & 0o111 else 0o644)


def complete_xmake_scripts(archive, output):
    # The release source tar omits files in the directory passed to Xmake's
    # embed rule. Restore that directory from the same release's Git commit.
    origin = json.loads((HERE / "xmake/UPSTREAM.json").read_bytes())
    prefix = PurePosixPath("xmake-" + origin["commit"], "xmake")
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != origin["script_tree"]["archive_sha256"]:
            raise ValueError("incorrect Xmake Git source archive")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:gz") as packed:
            for member in packed:
                path = PurePosixPath(member.name)
                if not path.is_relative_to(prefix) or member.isdir():
                    continue
                if ".." in path.parts or not member.isfile():
                    raise ValueError("unexpected Xmake script tree entry")
                target = output / "xmake" / path.relative_to(prefix)
                mode = 0o755 if member.mode & 0o111 else 0o644
                with packed.extractfile(member) as file:
                    data = file.read()
                if target.exists():
                    if target.read_bytes() != data:
                        raise ValueError("Xmake release scripts changed: " + path.as_posix())
                    target.chmod(mode)
                else:
                    put(target, data, mode)


def vm_product(relative):
    if relative.is_relative_to(OPENSSL_INPUT):
        parts = relative.relative_to(OPENSSL_INPUT).parts
        return parts[0] in OPENSSL_DIRS or (len(parts) == 1 and parts[0] in OPENSSL_FILES)
    if relative.is_relative_to("tools/dependencies"):
        return relative.name == "build_openssl.py"
    return True


def adapt_openssl(output):
    source = output / OPENSSL
    inventory = source / "sources.sha256"
    original = inventory.read_bytes()
    if hashlib.sha256(original).hexdigest() != OPENSSL_FULL_HASH:
        raise ValueError("unexpected VM OpenSSL release inventory")
    full = output.parent / "openssl-full-release.sha256"
    inventory.rename(full)

    # Configure reads a build.info in every SUBDIRS entry, including targets that
    # will never be compiled. Remove the application, fuzzer and manual graphs.
    graph = source / "upstream/build.info"
    original_graph = graph.read_bytes()
    old = b"SUBDIRS=crypto ssl apps util tools fuzz providers doc\n"
    if original_graph.count(old) != 1:
        raise ValueError("unexpected OpenSSL root build graph")
    graph.write_bytes(original_graph.replace(old, b"SUBDIRS=crypto ssl util tools providers\n"))
    retained = []
    for line in original.splitlines():
        expected, name = line.split(b"  ", 1)
        relative = PurePosixPath(name.decode("utf-8"))
        if not vm_product(OPENSSL / relative):
            continue
        file = source / relative
        with file.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest().encode("ascii")
        if relative == PurePosixPath("upstream/build.info"):
            if hashlib.sha256(original_graph).hexdigest().encode("ascii") != expected:
                raise ValueError("unrecognized OpenSSL library build graph")
        elif actual != expected:
            raise ValueError("modified upstream OpenSSL file: " + relative.as_posix())
        retained.append(actual + b"  " + name + b"\n")
    inventory.write_bytes(b"".join(retained))
    product_hash = hashlib.sha256(inventory.read_bytes()).hexdigest()
    builder = output / "tools/dependencies/build_openssl.py"
    original_builder = builder.read_text()
    old_flags = "'no-tests','no-apps','no-module',"
    if original_builder.count(OPENSSL_FULL_HASH) != 1 or original_builder.count(old_flags) != 1:
        raise ValueError("unexpected OpenSSL build recipe")
    builder.write_text(original_builder.replace(OPENSSL_FULL_HASH, product_hash)
                       .replace(old_flags, "'no-tests','no-apps','no-module','no-docs','no-demos',"))
    return product_hash


def import_vm(sources, listing, output):
    origin = json.loads((HERE / "uwvm2-ros/UPSTREAM.json").read_bytes())
    if listing:
        rows = listing.read_bytes()
    else:
        rows = subprocess.check_output(["git", "-C", sources, "ls-tree", "-rz", origin["commit"], "--", *VM_PATHS])
    if hashlib.sha256(rows).hexdigest() != VM_LIST_SHA256:
        raise ValueError("unexpected Git tree for the VM source inputs")
    for row in filter(None, rows.split(b"\0")):
        description, name = row.split(b"\t", 1)
        mode, kind, expected = description.decode("ascii").split()
        path = PurePosixPath(name.decode("utf-8"))
        if not vm_product(path):
            continue
        source = sources / path
        if mode not in ("100644", "100755") or kind != "blob" or source.is_symlink():
            raise ValueError("expected a regular Git source file: " + path.as_posix())
        data = source.read_bytes()
        actual = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
        if actual != expected:
            raise ValueError("modified VM source: " + path.as_posix())
        overlay = origin["source"]["sdk_portability_overlays_sha256"].get(path.as_posix())
        if overlay:
            data = (HERE / "uwvm2-ros/upstream" / path).read_bytes()
            if hashlib.sha256(data).hexdigest() != overlay:
                raise ValueError("modified SDK portability overlay: " + path.as_posix())
        put(output / path, data, int(mode, 8) & 0o777)
    return adapt_openssl(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xmake-archive", required=True, type=Path)
    parser.add_argument("--xmake-commit-archive", required=True, type=Path)
    parser.add_argument("--vm-source", required=True, type=Path, help="checkout or exact Git file export")
    parser.add_argument("--vm-ls-tree", type=Path, help="pinned git ls-tree -rz output for a Git file export")
    parser.add_argument("--output", required=True, type=Path, help="new directory to receive both source trees")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        import_xmake(args.xmake_archive, args.output / "xmake/upstream")
        complete_xmake_scripts(args.xmake_commit_archive, args.output / "xmake/upstream")
        product_hash = import_vm(args.vm_source, args.vm_ls_tree, args.output / "uwvm2-ros/upstream")
    except Exception:
        shutil.rmtree(args.output)
        raise
    print("OpenSSL product source manifest SHA-256", product_hash)


if __name__ == "__main__":
    main()
