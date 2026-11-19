"""Build the LLVM IR marker for the selected SDK backend toolchain."""
import argparse
from pathlib import Path
import shlex
import subprocess
import tempfile

from release import SDK, marker_path
from compiler import compiler_environment


def main():
    """Compile the narrow IR admission helper with optimization and symbols."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--toolchain", type=Path, required=True)
    p.add_argument("--host-cxx", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        toolchain = args.toolchain.resolve(strict=True)
        output = args.output or marker_path(toolchain)
        cfg = toolchain / "bin/llvm-config"
        env = compiler_environment(toolchain)

        def flags(*options):
            return shlex.split(subprocess.check_output([cfg, *options], env=env, text=True, timeout=15))

        with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
            staged = Path(scratch) / "wros-zig-mte"
            subprocess.run([args.host_cxx.absolute(), *flags("--cxxflags"), "-O3", "-g",
                            SDK / "language/zig/mark_mte.cpp",
                            *flags("--ldflags", "--libs", "core", "irreader", "bitwriter", "--system-libs"),
                            "-o", staged], env=env, check=True, timeout=180)
            staged.replace(output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        p.exit(1, f"prepare Zig marker: {error}\n")


if __name__ == "__main__":
    main()
