"""Read the pinned ABB ROS 1 .msg/.srv definitions in dependency order."""
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "upstream/ros1"
PACKAGES = ("abb_egm_msgs", "abb_rapid_msgs", "abb_rapid_sm_addin_msgs", "abb_robot_msgs")
PRIMITIVES = {"bool", "uint8", "uint16", "uint32", "float32", "float64", "time", "string"}


@dataclass(frozen=True)
class Field:
    name: str
    type: str   # primitive spelling or fully qualified package/type
    array: bool
    description: str


@dataclass(frozen=True)
class Constant:
    name: str
    type: str
    value: str  # genmsg val_text (string constant quotes are literal)
    description: str


@dataclass(frozen=True)
class Record:
    package: str
    name: str
    fields: tuple
    constants: tuple
    service: str | None   # name without Request/Response, or None for messages
    description: str

    @property
    def qualified(self):
        return f"{self.package}/{self.name}"


def _paragraphs(lines):
    paragraphs, current = [], []
    for line in lines:
        if line and line != "Note:":
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def _definition(lines, package, name):
    # ABB places the description and RAPID usage notes inside a ruled comment block.
    for i, line in enumerate(lines):
        if line.strip() == "# Description:":
            stop = next(j for j in range(i + 1, len(lines)) if lines[j].startswith("#---"))
            doc = _paragraphs([s.lstrip("#").strip() for s in lines[i + 1:stop]])
            return doc, lines[stop + 1:]
    if package == "std_msgs" and name == "Header":
        stop = next(i for i, line in enumerate(lines) if line.strip() == "#")
        return _paragraphs([s.lstrip("#").strip() for s in lines[:stop]]), lines[stop + 1:]
    if name == "ServiceResponses":
        return "Status strings and unsigned 16-bit result codes for ABB robot services.", lines[1:]
    raise ValueError(f"Unrecognized definition header for {package}/{name}")


def _body(package, name, lines, description, service=None):
    fields, constants = [], []
    pending, group_doc = [], ""
    for original in lines:
        stripped = original.strip()
        if not stripped or stripped.startswith("#---"):
            pending, group_doc = [], ""
            continue
        if stripped.startswith("#"):
            pending.append(stripped[1:].strip())
            continue
        line = original.partition("#")[0].strip()
        spelling, declaration = line.split(None, 1)
        if pending:
            group_doc = _paragraphs(pending)
            pending = []
        if "=" in declaration:
            identifier, _, value = declaration.partition("=")
            if spelling == "string":
                value = original.partition("=")[2]
            constants.append(Constant(identifier.strip(), spelling, value.strip(), group_doc))
            continue
        array = spelling.endswith("[]")
        base = spelling.removesuffix("[]")
        if "[" in base or "]" in base:
            raise ValueError(f"Unsupported ABB field type {spelling}")
        if base not in PRIMITIVES and "/" not in base:
            base = "std_msgs/Header" if base == "Header" else f"{package}/{base}"
        fields.append(Field(declaration, base, array, group_doc))
    return Record(package, name, tuple(fields), tuple(constants), service, description)


def load(root=SOURCE):
    """Return all ABB records plus Header. A service yields separate request and response records."""
    root = Path(root)
    records = {}
    def add(record):
        if record.qualified in records:
            raise ValueError(f"Duplicate ROS type {record.qualified}")
        records[record.qualified] = record

    header = root / "std_msgs/msg/Header.msg"
    desc, lines = _definition(header.read_text().splitlines(), "std_msgs", "Header")
    add(_body("std_msgs", "Header", lines, desc))
    for package in PACKAGES:
        files = sorted((root / package / "msg").glob("*.msg"))
        if not files:
            raise ValueError(f"No message definitions for {package} under {root}")
        for path in files:
            desc, lines = _definition(path.read_text().splitlines(), package, path.stem)
            add(_body(package, path.stem, lines, desc))
        for path in sorted((root / package / "srv").glob("*.srv")):
            desc, lines = _definition(path.read_text().splitlines(), package, path.stem)
            boundary, = (i for i, line in enumerate(lines) if line.strip() == "---")
            add(_body(package, path.stem + "Request", lines[:boundary], desc, path.stem))
            add(_body(package, path.stem + "Response", lines[boundary + 1:], desc, path.stem))

    ordered, visiting = {}, set()
    def visit(key):
        if key in ordered:
            return
        if key in visiting:
            raise ValueError(f"Recursive ROS type {key}")
        visiting.add(key)
        record = records[key]
        for field in record.fields:
            if field.type not in PRIMITIVES:
                visit(field.type)
        visiting.remove(key)
        ordered[key] = record
    for key in records:
        visit(key)
    return list(ordered.values())


def fingerprints(records):
    """Produce genmsg handshake MD5s keyed by message or service name."""
    hashes, bodies = {}, {}
    for record in records:
        lines = [f"{c.type} {c.name}={c.value}" for c in record.constants]
        for field in record.fields:
            spelling = field.type + ("[]" if field.array else "")
            if field.type not in PRIMITIVES:
                spelling = hashes[field.type]
            lines.append(f"{spelling} {field.name}")
        body = "\n".join(lines).encode()
        if record.service is None:
            hashes[record.qualified] = md5(body).hexdigest()
        else:
            bodies[record.qualified] = body
    for record in records:
        if record.service and record.name == record.service + "Request":
            name = f"{record.package}/{record.service}"
            hashes[name] = md5(bodies[name + "Request"] + bodies[name + "Response"]).hexdigest()
    return hashes
