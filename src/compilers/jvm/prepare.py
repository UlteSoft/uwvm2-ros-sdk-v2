"""Install a pinned upstream JDK and Maven inputs, then compile the WROS TeaVM classes."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import runpy
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
fetch_archive = runpy.run_path(str(HERE.parent / "official_dist.py"))["fetch_archive"]


def verify(path, size, expected):
    if path.stat().st_size != size:
        raise ValueError("size mismatch: " + str(path))
    with path.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != expected:
            raise ValueError("SHA-256 mismatch: " + str(path))


def unpack_temurin(archive, row, destination, work):
    tar = work / "temurin.tar"
    count = 0
    with gzip.open(archive, "rb") as src, tar.open("xb") as output:
        while data := src.read(1 << 20):
            count += len(data)
            if count > row["tar_bytes"]:
                raise ValueError("decompressed archive exceeds its declared size")
            output.write(data)
    verify(tar, row["tar_bytes"], row["tar_sha256"])
    destination.mkdir(parents=True, exist_ok=False)
    root = PurePosixPath(row["root"])
    seen = set()
    with tarfile.open(tar, "r:") as src:
        members = {item.name: item for item in src.getmembers()}
        for item in src.getmembers():
            path = PurePosixPath(item.name)
            if path.is_absolute() or ".." in path.parts or not path.is_relative_to(root):
                raise ValueError("unexpected archive path: " + item.name)
            name = path.relative_to(root).as_posix()
            if item.isdir():
                continue
            if name in seen or name == ".":
                raise ValueError("unexpected or duplicate archive file: " + name)
            seen.add(name)
            # The Temurin archive uses relative links between module license files.
            # Write verified regular bytes so an installation can be moved or inventoried.
            if item.issym():
                target = posixpath.normpath(posixpath.join(posixpath.dirname(item.name), item.linkname))
                if not PurePosixPath(target).is_relative_to(root):
                    raise ValueError("archive link points outside the JDK: " + name)
                item = members[target]
            if not item.isfile():
                raise ValueError("expected one regular archive member: " + name)
            out = destination / name
            out.parent.mkdir(parents=True, exist_ok=True)
            with src.extractfile(item) as stream, out.open("xb") as dst:
                shutil.copyfileobj(stream, dst, 1 << 20)
            out.chmod(0o755 if item.mode & 0o111 else 0o644)
    tar.unlink()
    for name, spec in row["members"].items():
        verify(destination / PurePosixPath(name).relative_to(root), spec["bytes"], spec["sha256"])


def install_inputs(rows, destination, cache):
    destination.mkdir(exist_ok=True)
    files = {}
    for row in rows:
        name = row["url"].rsplit("/", 1)[1]
        if name in ("", ".", "..") or name in files or name != row.get("name", name):
            raise ValueError("unexpected or duplicate upstream filename: " + name)
        target = destination / name
        if target.exists():
            verify(target, row["size"], row["sha256"])
        else:
            archive = fetch_archive(row["url"], row["sha256"], cache, size=row["size"])
            shutil.copyfile(archive, target)
            target.chmod(0o644)
        files[name] = target
    return list(files.values())


def prepare(sdk, host, platform, mode, work, cache=None):
    if mode != "source":
        raise ValueError("the WROS TeaVM driver and runtime classes require the explicit SDK rebuild action")
    cache = Path(cache or os.environ.get("WROS_DIST_CACHE", work / "sha256")).resolve()
    root = sdk / "src/compilers/jvm"
    core = root / "upstream/core/src/main"
    port = core / "java/org/teavm"
    records = json.loads((sdk / "bin/packages" / host / "wrjava/java.json").read_bytes())
    if records["host"] != host:
        raise ValueError("unexpected Java package host")
    jdk = sdk / "share/toolchains/jdk"
    toolchain = sdk / "share/toolchains/teavm"
    toolchain.mkdir(parents=True)
    jdk_lock = json.loads((sdk / records["jdk_lock"]).read_bytes())
    if host == "linux-x86_64":
        row = jdk_lock["official_downloads"]["jdk"]
        archive = fetch_archive(row["url"], row["sha256"], cache, size=row["size"])
        unpack_temurin(archive, row, jdk, work)
    else:
        debian = runpy.run_path(str(root / "package_inputs.py"))
        arch = debian["HOST_ARCH"][host]
        packages = jdk_lock["arches"][arch]["packages"]
        inputs = work / "java-debs"
        inputs.mkdir()
        for package in packages.values():
            archive = fetch_archive(package["url"], package["sha256"], cache, size=package["size"])
            (inputs / package["name"]).symlink_to(archive)
        for name, source in debian["jdk"](host, inputs, work).items():
            target = jdk / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o755 if os.access(source, os.X_OK) else 0o644)
        install_inputs(jdk_lock["source"], root / "openjdk/debian", cache)
    native = runpy.run_path(str(sdk / "install/install.py"))
    for file in jdk.rglob("*"):
        if file.is_file():
            with file.open("rb") as stream:
                if stream.read(4) == b"\x7fELF":
                    native["require_host"](file, host)
    for required in ("bin/java", "bin/javac", "bin/javap", "release", "lib/modules"):
        if not (jdk / required).is_file():
            raise ValueError("missing JDK component: " + required)
    jars = install_inputs(json.loads((root / "java-jars.json").read_bytes()), toolchain / "jars", cache)
    (toolchain / "jars.list").write_text("".join(jar.name + "\n" for jar in jars))
    install_inputs(json.loads((root / "java-source-jars.json").read_bytes()), toolchain / "source-jars", cache)
    # Verify the patched backend files and runtime templates against the port manifest.
    for patch in json.loads((root / "upstream.json").read_bytes())["local_changes"]:
        changed = root / "upstream" / patch["path"]
        verify(changed, changed.stat().st_size, patch["sdk_sha256"])
    host_classes, runtime = toolchain / "host", toolchain / "runtime"
    host_classes.mkdir()
    runtime.mkdir()
    env = dict(os.environ, TMPDIR=str(work))
    javac = [jdk / "bin/java", "-XX:-UsePerfData", "-Djava.io.tmpdir=" + str(work),
             "-m", "jdk.compiler/com.sun.tools.javac.Main", "-source", "21", "-target", "21", "-g",
             "-encoding", "UTF-8", "-proc:none", "-cp", os.pathsep.join(map(str, jars))]
    subprocess.run([*javac, "-d", host_classes, root / "driver/WrosJava.java", root / "driver/Translate.java",
                    port / "backend/c/CTarget.java", port / "backend/c/generate/ClassGenerator.java"], check=True, env=env)
    subprocess.run([*javac, "-d", runtime, port / "runtime/GC.java", port / "runtime/Allocator.java"], check=True, env=env)
    (toolchain / "platform").write_text(platform + "\n")
    paths = [host_classes, core / "resources", runtime, *jars]
    (toolchain / "classpath").write_text("".join("/" + str(path.relative_to(sdk)) + "\n" for path in paths))
    (sdk / "bin").mkdir(exist_ok=True)
    subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Os", root / "driver/wrjava.c",
                    "-o", sdk / "bin/wrjava"], check=True, env=env)
    native["require_host"](sdk / "bin/wrjava", host)


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--sdk", type=Path, required=True)
    arg.add_argument("--host", required=True)
    arg.add_argument("--platform", choices=("abb", "generic"), required=True)
    arg.add_argument("--mode", choices=("source",), required=True)
    arg.add_argument("--work", type=Path, required=True)
    arg.add_argument("--download-cache", type=Path, help="directory for verified, SHA-256-addressed upstream inputs")
    args = arg.parse_args()
    prepare(args.sdk.resolve(), args.host, args.platform, args.mode, args.work.resolve(), args.download_cache)
