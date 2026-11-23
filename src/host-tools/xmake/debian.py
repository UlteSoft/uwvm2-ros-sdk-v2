"""Install the published Debian Xmake ELF, matching scripts and private runtime."""
import io
import json
from pathlib import Path, PurePosixPath
import runpy
import shutil
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
RUNTIME = Path("libexec/xmake")
SCRIPTS = PurePosixPath("usr/share/xmake")

# Xmake starts copies of itself through os.programfile(). Keep that path on
# the launcher so every child receives the same loader and script directory.
LAUNCHER = """#!/bin/sh
set -eu
XMAKE_PROGRAM_FILE=$(readlink -f -- "$0")
runtime=${XMAKE_PROGRAM_FILE%/bin/xmake}/libexec/xmake
export XMAKE_PROGRAM_FILE
export XMAKE_PROGRAM_DIR="$runtime/share/xmake"
exec "$runtime/lib/@LOADER@" --inhibit-cache --library-path '$ORIGIN/../lib' "$runtime/bin/xmake" "$@"
"""


def package_data(archive):
    """Read the data.tar.xz member of a verified Debian ar archive."""
    length = archive.stat().st_size
    with archive.open("rb") as stream:
        if stream.read(8) != b"!<arch>\n":
            raise ValueError(f"invalid Debian archive: {archive}")
        while header := stream.read(60):
            if len(header) != 60 or header[-2:] != b"`\n":
                raise ValueError(f"invalid Debian archive header: {archive}")
            size = int(header[48:58])
            if size < 0 or stream.tell() + size > length:
                raise ValueError(f"invalid Debian archive member size: {archive}")
            if header[:16].rstrip(b" /") == b"data.tar.xz":
                return io.BytesIO(stream.read(size))
            stream.seek(size + size % 2, 1)
    raise ValueError(f"missing Debian data.tar.xz: {archive}")


def unpack_package(archive, members, root, *, scripts=False):
    """Copy regular payload members directly under their installed names."""
    missing = set(members)
    script_count = 0
    with package_data(archive) as data, tarfile.open(fileobj=data, mode="r|xz") as tar:
        for item in tar:
            path = PurePosixPath(item.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("invalid Debian package path: " + item.name)
            if item.isdir():
                continue
            if path.as_posix() in members:
                output = root / members[path.as_posix()]
                missing.discard(path.as_posix())
            elif scripts and path.is_relative_to(SCRIPTS):
                output = root / "share/xmake" / path.relative_to(SCRIPTS)
                script_count += 1
            else:
                continue
            if not item.isfile():
                raise ValueError("expected a regular Debian package member: " + item.name)
            output.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(item) as source, output.open("xb") as dest:
                shutil.copyfileobj(source, dest)
            output.chmod(0o755 if item.mode & 0o111 else 0o644)
    if missing:
        raise ValueError(f"missing Debian package files in {archive}: {sorted(missing)}")
    return script_count


def install(host, sdk, work, cache):
    """Populate an SDK staging tree and return the verified binary's provenance."""
    lock = json.loads((HERE / "debian-packages.json").read_bytes())
    if lock["schema"] != 1 or host not in lock["hosts"]:
        raise ValueError("no locked Debian Xmake for " + host)
    selected = lock["hosts"][host]
    packages = {**selected["packages"], **lock["shared_packages"]}
    fetch_archive = runpy.run_path(str(HERE.parents[1] / "compilers/official_dist.py"))["fetch_archive"]
    native = runpy.run_path(str(HERE.parents[2] / "install/install.py"))
    target = Path(sdk) / RUNTIME
    shim = Path(sdk) / "bin/xmake"
    if target.exists() or shim.exists():
        raise FileExistsError(f"Xmake already exists in staging tree {sdk}")
    with tempfile.TemporaryDirectory(dir=work, prefix="debian-xmake-") as temporary:
        root = Path(temporary) / "xmake"
        script_count = 0
        for name, package in packages.items():
            archive = fetch_archive(lock["snapshot"] + package["pool_path"], package["sha256"], cache,
                                    size=package["size"])
            members = {src.format_map(selected): dst.format_map(selected)
                       for src, dst in lock["members"][name].items()}
            script_count += unpack_package(archive, members, root, scripts=name == "xmake-data")
        if script_count != lock["script_files"] or not (root / "share/xmake/core/_xmake_main.lua").is_file():
            raise ValueError("incomplete Debian Xmake program directory")
        program = root / "bin/xmake"
        for elf in (program, *(root / "lib").iterdir()):
            native["require_host"](elf, host)
        actual = native["digest"](program)
        if actual != selected["elf_sha256"]:
            raise ValueError("Debian Xmake ELF differs from the release lock")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root), target)
        shim.parent.mkdir(parents=True, exist_ok=True)
        shim.write_text(LAUNCHER.replace("@LOADER@", selected["loader"]))
        shim.chmod(0o755)
    return {"provider": "debian", "host": host, "version": selected["version"],
            "path": (RUNTIME / "bin/xmake").as_posix(), "sha256": actual, "shim": "bin/xmake",
            "snapshot": lock["snapshot"], "packages": packages}
