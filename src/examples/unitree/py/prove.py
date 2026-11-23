#!/usr/bin/env python3
"""Exercise a publicly installed Python SDK from a new external project directory."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True, help="parent directory outside the SDK")
    args = parser.parse_args()
    sdk, work = args.sdk.resolve(), args.work.resolve()
    if work == sdk or sdk in work.parents:
        parser.error("choose a work directory outside the installation")
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(sdk), PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(dir=work, prefix="unitree-python-") as directory:
        project = Path(directory)
        env.update(TMPDIR=str(project), XMAKE_TMPDIR=str(project / ".xmake-temp"),
                   XMAKE_GLOBALDIR=str(project / ".xmake-global"))
        program = project / "independent.py"
        program.write_text("import sys, math\nassert sys.version_info[:3] == (3,14,8)\n"
                           "class Window(list):\n    def magnitude(self): return math.sqrt(sum(x*x for x in self))\n"
                           "assert Window([3,4]).magnitude() == 5\nprint('shared-cpython-ok')\n")
        for engine in ("int", "aot"):
            result = subprocess.run([sys.executable, "-I", "-B", sdk / "bin/wrpy.py", "--run", engine, program],
                                    cwd=project, env=env, check=True, stdout=subprocess.PIPE)
            if b"shared-cpython-ok" not in result.stdout:
                raise ValueError("shared guest did not emit its Python completion marker")
            sys.stdout.buffer.write(result.stdout)
        for name in ("main.py", "vectors.py", "xmake.lua"):
            shutil.copyfile(sdk / "examples/unitree/py" / name, project / name)
        for command in (["build"], ["test", "-j1"]):
            subprocess.run([sdk / "bin/xmake", *command], cwd=project, env=env, check=True)


if __name__ == "__main__":
    main()
