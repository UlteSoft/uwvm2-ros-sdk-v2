"""Build an external Java application with the repository's TeaVM C port and installed WROS C SDK."""
import argparse
from contextlib import nullcontext
from hashlib import file_digest
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request


HERE = Path(__file__).resolve().parent
CORE = HERE / "upstream/core/src/main"
DRIVER = HERE / "driver"


def verified(path, artifact):
    if path.stat().st_size != artifact["size"]:
        return False
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest() == artifact["sha256"]


def jars(cache, offline):
    """Use the same verified Maven artifacts for online and offline builds."""
    paths = []
    cache.mkdir(parents=True, exist_ok=True)
    for artifact in json.loads((HERE / "java-jars.json").read_text()):
        url = artifact["url"]
        path = cache / url.rsplit("/", 1)[1]
        if path.exists():
            if not verified(path, artifact):
                raise ValueError(f"size or SHA-256 mismatch for {path}")
        elif offline:
            raise ValueError(f"missing offline artifact {path}")
        else:
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as pending:
                pending_path = Path(pending.name)
            try:
                with urllib.request.urlopen(url, timeout=90) as source, pending_path.open("wb") as output:
                    remaining = artifact["size"]
                    while remaining:
                        block = source.read(min(remaining, 1024 * 1024))
                        if not block:
                            raise ValueError(f"short download for {url}")
                        output.write(block)
                        remaining -= len(block)
                    if source.read(1):
                        raise ValueError(f"oversize download for {url}")
                if not verified(pending_path, artifact):
                    raise ValueError(f"SHA-256 mismatch for {url}")
                os.replace(pending_path, path)
            finally:
                pending_path.unlink(missing_ok=True)
        paths.append(path)
    return paths


def classpath(paths):
    return os.pathsep.join(map(str, paths))


def build(args, work, artifacts, sources):
    host = work / "translator"
    runtime = work / "runtime"
    app = work / "classes"
    generated = work / "generated"
    scratch = work / "tmp"
    for directory in (host, runtime, app, generated, scratch):
        directory.mkdir()
    env = dict(os.environ, TMPDIR=str(scratch))
    java = [args.jdk / "bin/java", "-XX:-UsePerfData", f"-Djava.io.tmpdir={scratch}"]
    # This is OpenJDK's javac entry point. Some distribution images keep the
    # compiler module but omit its bin/javac launcher and historical ct.sym.
    javac = [*java, "-m", "jdk.compiler/com.sun.tools.javac.Main", "-source", "21", "-target", "21",
             "-encoding", "UTF-8", "-proc:none", "-g"]
    cp = classpath(artifacts)
    teavm = CORE / "java/org/teavm"
    subprocess.run([*javac, "-cp", cp, "-d", host, DRIVER / "Translate.java",
                    teavm / "backend/c/CTarget.java", teavm / "backend/c/generate/ClassGenerator.java"],
                   check=True, env=env)
    subprocess.run([*javac, "-cp", cp, "-d", runtime, teavm / "runtime/GC.java",
                    teavm / "runtime/Allocator.java"], check=True, env=env)
    subprocess.run([*javac, "-cp", classpath([runtime, *artifacts]), "-d", app, *sources],
                   check=True, env=env)
    main = app.joinpath(*args.main_class.split(".")).with_suffix(".class")
    with main.open("rb") as compiled:
        if compiled.read(4) != b"\xca\xfe\xba\xbe":
            raise ValueError(f"missing Java class file for {args.main_class}")
    inputs = [runtime, app, *artifacts]
    # CTarget resolves its C templates through its defining class loader. Its patched
    # classes, resources and the guest collector must take precedence over the release JARs.
    host_cp = classpath([host, CORE / "resources", *inputs])
    subprocess.run([*java, "-cp", host_cp, "Translate", "C", generated, classpath(inputs), args.main_class],
                   check=True, env=env)
    # Put the launcher beside all.c. A global -I for this directory would also
    # shadow the system <time.h> and <string.h> with TeaVM's private headers.
    entry = generated / "wros_entry.c"
    shutil.copyfile(DRIVER / "entry.c", entry)
    linked = work / "linked.wasm"
    subprocess.run([args.c_sdk / "bin/wrc", "--target", "wasm32", "--core", "3.0", "--eh", "--mte",
                    "--reactor", "--export", "_start", "-O2", "-D", "__WASM_MEMTAG__=1",
                    entry, "-o", linked], check=True, env=env)
    with linked.open("rb") as wasm:
        if wasm.read(8) != b"\0asm\x01\0\0\0":
            raise ValueError("the WROS compiler did not produce a Core WebAssembly module")
    # The diagnostic directory may live on a different filesystem to the output.
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as pending:
        pending_path = Path(pending.name)
    try:
        shutil.copyfile(linked, pending_path)
        os.replace(pending_path, args.output)
    finally:
        pending_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk", required=True, type=Path, help="OpenJDK 21 home with bin/java and the jdk.compiler module")
    parser.add_argument("--c-sdk", required=True, type=Path, help="installed C SDK containing bin/wrc and its sysroot")
    parser.add_argument("--jars", required=True, type=Path, help="directory for the SHA-256-locked compiler JARs")
    parser.add_argument("--offline", action="store_true", help="require all locked JARs to be present")
    parser.add_argument("--main-class", required=True, help="binary name of the Java main class")
    parser.add_argument("--source-root", required=True, action="append", type=Path,
                        help="compile .java files in this source directory (repeat for dependencies)")
    parser.add_argument("--keep-work", type=Path, help="retain .class files and generated C in this new directory")
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()
    if not all(part.replace("$", "_").isidentifier() for part in args.main_class.split(".")):
        parser.error("expected the Java binary name of a main class")
    roots = [root.resolve(strict=True) for root in args.source_root]
    roots.append(HERE.parents[2] / "include/u2rosv2/universal/java/src")
    sources = set()
    for root in roots:
        files = list(root.rglob("*.java")) if root.is_dir() else []
        if not files:
            parser.error(f"no Java sources under {root}")
        sources.update(file.resolve(strict=True) for file in files)
    args.output = args.output.absolute()
    if args.output.suffix != ".wasm":
        parser.error("expected a .wasm output filename")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.jdk = args.jdk.resolve(strict=True)
    args.c_sdk = args.c_sdk.resolve(strict=True)
    release = (args.jdk / "release").read_text().splitlines()
    if not any(line == 'JAVA_VERSION="21"' or line.startswith('JAVA_VERSION="21.') for line in release):
        parser.error(f"this producer requires an OpenJDK 21 image: {args.jdk}")
    for program in (args.jdk / "bin/java", args.c_sdk / "bin/wrc"):
        if not program.is_file() or not os.access(program, os.X_OK):
            parser.error(f"missing executable {program}")
    artifacts = jars(args.jars.resolve(), args.offline)
    if args.keep_work:
        work = args.keep_work.resolve()
        work.mkdir(parents=True, exist_ok=False)
        stage = nullcontext(work)
    else:
        stage = tempfile.TemporaryDirectory(prefix=".java-build-", dir=args.output.parent)
    with stage as directory:
        build(args, Path(directory), artifacts, sorted(sources))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"Java guest build failed: {error}")
