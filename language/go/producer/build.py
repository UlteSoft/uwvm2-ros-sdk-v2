"""@brief Rebuild wrgo's Wasm-only compiler from two pinned Go release archives."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_SHA = "9dc77ffadc16d837a1bf32d99c624cb4df0647cee7b119edd9e7b1bcc05f2e00"
BOOTSTRAP_SHA = "68097bd680839cbc9d464a0edce4f7c333975e27a90246890e9f1078c7e702ad"
GENERATED = {
    "src/go/build/zcgo.go",
    "src/internal/buildcfg/zbootstrap.go",
    "src/internal/runtime/sys/zversion.go",
    "src/cmd/internal/objabi/zbootstrap.go",
}


def digest(path):
    """@brief Return the SHA-256 of a local build input."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build(source, bootstrap, output):
    """@brief Build a Linux/amd64 host program with a single wasm32 guest target.
    @param source Official Go 1.24.2 source release archive.
    @param bootstrap Matching upstream Linux/amd64 archive for the host bootstrap.
    @param output New output directory for the compiler and its input hashes.
    @details Private build files are removed on failure. No network is used.
    """
    if digest(source) != SOURCE_SHA or digest(bootstrap) != BOOTSTRAP_SHA:
        raise ValueError("Go source or bootstrap release digest differs")
    if output.exists():
        raise ValueError("choose a new producer output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as work:
        work = Path(work)
        src = work / "go"
        product = work / "producer"
        product.mkdir()
        with tarfile.open(source, "r:gz") as archive:
            archive.extractall(work, filter="data")
        with tarfile.open(bootstrap, "r:gz") as archive:
            for entry in archive:
                if entry.isfile() and entry.name.startswith("go/"):
                    path = entry.name[3:]
                    if path == "bin/go" or path.startswith(("pkg/include/", "pkg/tool/linux_amd64/")) or path in GENERATED:
                        archive.extract(entry, work, filter="data")
        compiler = src / "src/cmd/compile"
        ssa = compiler / "internal/ssa"
        shutil.copyfile(HERE / "main.go", compiler / "main.go")
        shutil.copyfile(HERE / "proof.go", ssa / "wros.go")
        phases = ssa / "compile.go"
        text = phases.read_text()
        dispatch = "\t\tp.fn(f)\n"
        declaration = "\tconst logMemStats = false\n"
        if text.count(dispatch) != 1 or text.count(declaration) != 1:
            raise ValueError("unexpected Go compiler phase dispatch")
        hook = """		if p.name == "opt" {
			for _, b := range f.Blocks {
				if b.Kind == BlockExit {
					wrosDeferred = true
					break
				}
			}
			if !wrosDeferred {
				wrosWriteRegisters(f)
			}
		}
		if p.name == "early fuse" && wrosDeferred {
			// Remove blocks that the upstream prove pass made unreachable.
			deadcode(f)
			wrosWriteRegisters(f)
		}
"""
        text = text.replace(declaration, declaration + "\tvar wrosDeferred bool\n")
        phases.write_text(text.replace(dispatch, dispatch + hook))
        config = ssa / "config.go"
        text = config.read_text()
        first = text.index('\tcase "amd64":', text.index("func NewConfig("))
        last = text.index('\tcase "wasm":', first)
        config.write_text(text[:first] + text[last:])
        env = dict(PATH="/usr/bin:/bin", GOROOT=str(src), GOOS="linux", GOARCH="amd64",
                   GOENV="off", CGO_ENABLED="0", GOTOOLCHAIN="local", GOWORK="off",
                   GOPROXY="off", GOSUMDB="off", GOCACHE=str(work / "cache"),
                   GOPATH=str(work / "gopath"), TMPDIR=str(work))
        binary = product / "wrgo-producer"
        subprocess.run([src / "bin/go", "build", "-p", "4", "-trimpath", "-ldflags=-s -w -buildid=",
                        "-buildvcs=false", "-o", binary, "cmd/compile"], cwd=src / "src", env=env, check=True)
        record = dict(source_sha256=SOURCE_SHA, bootstrap_sha256=BOOTSTRAP_SHA, binary_sha256=digest(binary),
                      inputs={name: digest(HERE / name) for name in ("main.go", "proof.go", "build.py")})
        (product / "producer.json").write_text(json.dumps(record, indent=2) + "\n")
        product.rename(output)


def main():
    """@brief Validate the fixed release inputs and publish a completed build."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "bootstrap", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        build(args.source, args.bootstrap, args.output.resolve())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
