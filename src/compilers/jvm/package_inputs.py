"""Reproduce the architecture-neutral Maven bundles and Debian JDK images from locked inputs."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import runpy
import subprocess
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
HOST_ARCH = {"linux-i686": "i386", "linux-aarch64": "arm64", "linux-arm": "armel", "linux-armhf": "armhf"}
JDK_OMITTED_LINKS = {"lib/src.zip", "lib/security/cacerts"}
NATIVE = runpy.run_path(str(HERE.parents[2] / "install/install.py"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(path, row):
    if path.stat().st_size != row["size"] or digest(path) != row["sha256"]:
        raise ValueError("input size or SHA-256 mismatch: " + str(path))


def archive(files, output, work):
    tar = work / "host.tar"
    with tarfile.open(tar, "w", format=tarfile.USTAR_FORMAT) as packed:
        for name, path in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size = path.stat().st_size
            member.mode = 0o755 if os.access(path, os.X_OK) else 0o644
            with path.open("rb") as stream:
                packed.addfile(member, stream)
    pending = work / "host.tar.xz"
    with pending.open("wb") as out:
        subprocess.run(["xz", "-6", "-T2", "--block-size=16MiB", "--check=crc64", "-c", tar], stdout=out, check=True)
    row = dict(format="tar.xz", tar_bytes=tar.stat().st_size, tar_sha256=digest(tar),
               compressed_bytes=pending.stat().st_size, compressed_sha256=digest(pending))
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(pending, output)
    return row


def resolved_member(root, path):
    """Resolve a Debian absolute link in the unpacked package namespace."""
    for _ in range(32):
        if not path.is_relative_to(root):
            break
        if not path.is_symlink():
            if path.is_file() and path.resolve().is_relative_to(root):
                return path
            break
        target = os.readlink(path)
        path = Path(os.path.normpath(root / target.lstrip("/") if target.startswith("/") else path.parent / target))
    raise ValueError("unresolved Debian member: " + str(path))


def jdk(host, inputs, work):
    arch = HOST_ARCH[host]
    meta = json.loads((HERE / "openjdk/debian/upstream.json").read_text())["arches"][arch]
    tree = work / "debian"
    tree.mkdir()
    for package in meta["packages"].values():
        deb = inputs / package["name"]
        verify(deb, package)
        subprocess.run(["dpkg-deb", "--extract", deb, tree], check=True)
    home = tree / "usr/lib/jvm" / ("java-21-openjdk-" + arch)
    files = {}
    for item in sorted(home.rglob("*")):
        name = item.relative_to(home).as_posix()
        if (name not in ("bin/java", "bin/javac", "bin/javap", "release") and not name.startswith(("lib/", "legal/", "conf/"))
                or name in JDK_OMITTED_LINKS or item.is_dir()):
            continue
        real = resolved_member(tree, item)
        with real.open("rb") as stream:
            if stream.read(4) == b"\x7fELF":
                NATIVE["require_host"](real, host)
        files[name] = real
    files["legal/debian-copyright"] = tree / "usr/share/doc/openjdk-21-jre-headless/copyright"
    if not {"release", "bin/java", "bin/javac", "bin/javap", "lib/modules"} <= files.keys():
        raise ValueError("incomplete Debian JDK")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("jars", "source-jars", *HOST_ARCH), required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.work.resolve(), prefix="java-package-") as temporary:
        work = Path(temporary)
        if args.kind in HOST_ARCH:
            files = jdk(args.kind, args.inputs, work)
        else:
            files = {}
            for row in json.loads((HERE / ("java-" + args.kind + ".json")).read_text()):
                name = row["url"].rsplit("/", 1)[1]
                item = args.inputs / name
                verify(item, row)
                files[name] = item
        print(json.dumps(archive(files, args.output, work), indent=2))


if __name__ == "__main__":
    main()
