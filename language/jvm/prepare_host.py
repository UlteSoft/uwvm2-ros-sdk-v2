#!/usr/bin/env python3
"""Assemble a pinned Linux x86-64 compiler host for one selected JVM language."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen


def copy_verified(source, destination, row):
    remaining = row["bytes"]
    digest = hashlib.sha256()
    with destination.open("xb") as output:
        while remaining:
            data = source.read(min(remaining, 1024 * 1024))
            if not data:
                raise ValueError("incomplete host file: " + row["path"])
            output.write(data)
            digest.update(data)
            remaining -= len(data)
        if source.read(1) or digest.hexdigest() != row["sha256"]:
            raise ValueError("pinned host file mismatch: " + row["path"])
    destination.chmod(0o755 if row["executable"] else 0o644)


def prepare(args):
    manifest = Path(__file__).resolve().parents[1] / args.language / "host-inputs.json"
    if not manifest.is_file():
        raise ValueError("the selected language package is not installed")
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("host bundle output already exists")
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".wros-jvm-host-") as stage:
        bundle = Path(stage) / "bundle"
        for row in json.loads(manifest.read_text())["files"]:
            path = Path(row["path"])
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("invalid pinned host path")
            if path.parts[0] == "jdk21":
                source = args.jdk / path.relative_to("jdk21")
            elif path.parts[:2] == ("lib", "host-runtime"):
                source = args.system_libs / path.relative_to("lib/host-runtime")
            elif path.parts[0] == "compiler-jars" and len(path.parts) == 2:
                url = urlsplit(row["source"])
                if (url.scheme != "https" or url.netloc != "repo.maven.apache.org" or url.query
                        or url.fragment or not url.path.startswith("/maven2/") or Path(url.path).name != path.name):
                    raise ValueError("invalid pinned Maven URL")
                source = args.jars / path.name if args.jars else None
                cache_file = args.maven_cache / url.path.removeprefix("/maven2/")
                if source is None or not source.is_file():
                    source = cache_file
            else:
                raise ValueError("unsupported host input category")
            dest = bundle / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if source.is_file():
                stream = source.open("rb")
            elif path.parts[0] == "compiler-jars" and args.fetch_missing_jars:
                stream = urlopen(row["source"], timeout=60)
            else:
                raise ValueError("missing local compiler input: " + str(source))
            with stream:
                copy_verified(stream, dest, row)
        bundle.rename(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", choices=("java", "kotlin"))
    parser.add_argument("--jdk", type=Path, required=True, help="pinned Ubuntu OpenJDK installation")
    parser.add_argument("--system-libs", type=Path, required=True, help="pinned Linux x86-64 shared libraries")
    parser.add_argument("--jars", type=Path, help="optional flat directory containing pinned Maven JARs")
    parser.add_argument("--maven-cache", type=Path, default=Path.home() / ".m2/repository")
    parser.add_argument("--fetch-missing-jars", action="store_true", help="download missing selected JARs from Maven Central")
    parser.add_argument("--output", type=Path, required=True, help="new directory under an existing parent")
    args = parser.parse_args()
    try:
        prepare(args)
    except (OSError, ValueError) as error:
        parser.exit(1, f"prepare_host: {error}\n")


if __name__ == "__main__":
    main()
