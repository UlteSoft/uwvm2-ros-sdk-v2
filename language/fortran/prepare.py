"""Build the host-side LLVM IR marker against the selected SDK code generator."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "install"))
from compiler import compiler_environment, digest

SOURCE = HERE / "mark_mte.cpp"


def receipt_path(marker):
    return marker.with_name(marker.name + ".json")


def marker_identity(marker, toolchain):
    """Bind the helper to the locally trusted SDK source, binary and LLVM build."""
    return dict(format="wros-flang-mte", source_sha256=digest(SOURCE),
                codegen_sha256=digest(toolchain / "bin/clang"), marker_sha256=digest(marker))


def require_marker(marker, toolchain):
    receipt = receipt_path(marker)
    if not receipt.is_file() or receipt.stat().st_size > 1024:
        raise ValueError("missing or invalid helper receipt; run language/fortran/prepare.py")
    if json.loads(receipt.read_bytes()) != marker_identity(marker, toolchain):
        raise ValueError("MTE helper, source or code generator changed; rebuild the helper")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("--host-cxx", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="defaults to TOOLCHAIN/bin/wros-flang-mte")
    args = parser.parse_args()
    try:
        tc = args.toolchain.resolve(strict=True)
        marker = (args.output or tc / "bin/wros-flang-mte").resolve()
        env = compiler_environment(tc)
        cfg = tc / "bin/llvm-config"
        def settings(*options):
            return shlex.split(subprocess.check_output([cfg, *options], text=True, env=env))
        with tempfile.TemporaryDirectory(dir=marker.parent) as scratch:
            tmp = Path(scratch)
            binary = tmp / marker.name
            subprocess.run([args.host_cxx.resolve(strict=True), *settings("--cxxflags"), "-O3", "-g",
                            SOURCE, *settings("--ldflags", "--libs", "core", "irreader", "bitwriter", "--system-libs"),
                            "-o", binary], check=True, env=env)
            record = receipt_path(binary)
            record.write_text(json.dumps(marker_identity(binary, tc), indent=2) + "\n")
            # A reader overlapping either replacement can only see a matching pair or fail closed.
            binary.replace(marker)
            record.replace(receipt_path(marker))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"prepare: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
