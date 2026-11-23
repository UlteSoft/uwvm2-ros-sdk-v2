"""Generate Python slots and XCDR1 field order from the vendored Unitree .msg files."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generate_go import SCALAR, SOURCE, fields

DEST = HERE.parents[2] / "include/u2rosv2/platform/unitree/py"


def main():
    for package in sorted(SOURCE.glob("unitree_*")):
        schemas = {path.stem: fields(path) for path in sorted((package / "msg").glob("*.msg"))}
        output = DEST / package.name
        (output / "msg").mkdir(parents=True, exist_ok=True)
        (output / "__init__.py").write_text(f'"""Python representation of {package.name} ROS 2 messages."""\n')
        code = [f'"""Unitree ROS 2 v0.3.0 {package.name} message definitions."""',
                "from unitree_cdr import Message", ""]
        for name, rows in schemas.items():
            slots = tuple(row[2] for row in rows)
            code += ["", f"class {name}(Message):", f'    """{package.name}/msg/{name} in ROS field order."""',
                     f"    __slots__ = {slots!r}", "    _fields = ("]
            for kind, count, field in rows:
                if kind not in SCALAR and kind not in schemas:
                    raise ValueError(f"unresolved {kind} in {package.name}/{name}")
                length = None if count is None else int(count or -1)
                code.append(f"        ({field!r}, {kind!r}, {length!r}),")
            code += ["    )", ""]
        (output / "msg/__init__.py").write_text("\n".join(code))


if __name__ == "__main__":
    main()
