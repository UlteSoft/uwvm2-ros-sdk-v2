"""Pack the native Zig frontend and storage pass as independently selected Linux executables."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from package_native import file_hash, package

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--frontend", type=Path, required=True)
p.add_argument("--marker", type=Path, required=True)
p.add_argument("--work", type=Path, required=True)
args = p.parse_args()
host = "linux-x86_64"
packages = {}
out = ROOT / "bin/packages" / host / "wrzig"
out.mkdir(parents=True, exist_ok=True)
args.work.mkdir(parents=True, exist_ok=True)
for name, executable in (("wrzig", args.frontend), ("wros-zig-mte", args.marker)):
    filename = f"{name}-{file_hash(executable)[:20]}.tar.xz"
    temp = args.work / filename
    entry = package(executable, name, temp, host=host)
    target = out / filename
    temp.replace(target)
    entry.update(path=target.relative_to(ROOT).as_posix(), host=host)
    packages[name] = entry
(out / "release.json").write_text(json.dumps(dict(schema=1, host=host, packages=packages), indent=2) + "\n")
