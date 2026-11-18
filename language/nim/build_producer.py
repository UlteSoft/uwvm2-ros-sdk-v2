"""Build the private wasm32/wasm64 Nim source producer from pinned upstream sources."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "third-parties/nim/nim-2.2.4.tar.xz"
PIN = "f82b419750fcce561f3f897a0486b180186845d76fb5d99f248ce166108189c7"


LIB_ARCHIVE = ARCHIVE.with_name("nim-2.2.4-lib.tar.xz")
LIB_PIN = "ec55353f6db5332912c951095b5a7425513811ae9f760851a77d27c42e0182d0"


def unpack(where, only_library=False):
    archive, pin = (LIB_ARCHIVE, LIB_PIN) if only_library else (ARCHIVE, PIN)
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != pin:
            raise ValueError("Nim source archive digest mismatch")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r|xz") as archive:
            for entry in archive:
                path = Path(entry.name)
                if path.parts[:1] != ("nim-2.2.4",) or ".." in path.parts:
                    raise ValueError("invalid upstream path")
                if len(path.parts) < 2 or path.parts[1] not in ({"lib"} if only_library else {"compiler", "dist", "lib", "doc", "config"}):
                    continue
                if not entry.isfile():
                    continue
                output = where.joinpath(*path.parts[1:])
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as dest:
                    shutil.copyfileobj(archive.extractfile(entry), dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args()
    with tempfile.TemporaryDirectory(dir=options.output.parent) as td:
        work = Path(td).resolve()
        unpack(work)
        cpu = work / "compiler/platform.nim"
        original = cpu.read_text()
        enum = "cpuEsp, cpuWasm32,"
        row = '(name: "wasm32", intSize: 32, endian: littleEndian, floatSize: 64, bit: 32),'
        if original.count(row) != 1 or original.count(enum) != 1:
            raise ValueError("unexpected upstream target table")
        cpu.write_text(original.replace(enum, enum + " cpuWasm64,").replace(row, row + "\n    " + row.replace("32", "64")))
        source = work / "compiler/wrnim_lower.nim"
        shutil.copyfile(ROOT / "language/nim/wrnim_lower.nim", source)
        subprocess.run([options.bootstrap.resolve(strict=True), "c", "--skipUserCfg", "--skipParentCfg",
                        "--threads:off", "--parallelBuild:4", "-d:release", "-d:leanCompiler", "-d:nimcore",
                        "--lib:" + str(work / "lib"), "--nimcache:" + str(work / "cache"),
                        "--out:" + str(work / "producer"), source], check=True, cwd=work)
        (work / "producer").replace(options.output)


if __name__ == "__main__":
    main()
