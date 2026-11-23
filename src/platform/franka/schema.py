"""Read the pinned ROS 2 declarations and expand the Jazzy rosidl service/action records."""
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE / "upstream"
PRIMITIVES = {"bool": 1, "char": 1, "uint8": 1, "int8": 1, "uint32": 4,
              "int32": 4, "int64": 8, "float64": 8, "string": 5}
TYPE_PATTERN = re.compile(r"(\w+(?:/\w+)?)(?:\[(\d*)\])?")
VENDOR_COUNTS = {"franka_msgs": (6, 7, 5), "franka_spine_msgs": (4, 7, 1)}


@dataclass(frozen=True)
class Field:
    name: str
    base: str
    form: str = "single"
    count: int = 0
    default: str = ""
    doc: str = ""


@dataclass(frozen=True)
class Record:
    name: str
    fields: tuple
    constants: tuple
    source: str
    derived: bool = False


def field(name, base, description):
    return Field(name, base, doc=description)


def error_descriptions():
    header = UPSTREAM / "references/libfranka/include/franka/errors.h"
    comments = re.findall(r"/\*\*((?:(?!\*/).)*)\*/\s*const bool&\s*(\w+)\s*;", header.read_text(), re.S)
    return {
        name: " ".join(line.lstrip().removeprefix("*").strip() for line in doc.splitlines()).strip().replace("i.e.\\", "i.e.")
        for doc, name in comments
    }


def parse_section(pkg, lines, notes, errors, record_name):
    fields, constants, comments = [], [], []
    for original in lines:
        declaration, sep, inline = original.partition("#")
        declaration = declaration.strip()
        if not declaration:
            if sep:
                comments.append(inline.lstrip("#").strip())
            else:
                comments.clear()
            continue
        spelling, detail = declaration.split(None, 1)
        match = TYPE_PATTERN.fullmatch(spelling)
        if match is None:
            raise ValueError(f"Unexpected ROS field type {spelling}")
        base, array = match.groups()
        if base not in PRIMITIVES:
            parts = base.split("/")
            base = f"{parts[0] if len(parts) == 2 else pkg}/msg/{parts[-1]}"
        if "=" in detail:
            name, value = (s.strip() for s in detail.split("=", 1))
            doc = notes.get(record_name, {}).get(name) or " ".join(filter(None, [*comments, inline.strip()])).strip()
            if not doc:
                raise ValueError(f"Missing constant documentation for {record_name}.{name}")
            constants.append((name, base, value, doc))
        else:
            parts = detail.split()
            name = parts[0]
            default = parts[1] if len(parts) == 2 else ""
            desc = " ".join(filter(None, [*comments, inline.strip()])).strip()
            if record_name == "franka_msgs/msg/Errors":
                desc = errors[name]
            desc = notes.get(record_name, {}).get(name, desc)
            if not desc:
                desc = notes.get("*", {}).get(name, "")
            if not desc:
                raise ValueError(f"Missing field documentation for {record_name}.{name}")
            form = "single" if array is None else "sequence" if array == "" else "fixed"
            fields.append(Field(name, base, form, int(array or 0), default, desc))
        comments.clear()
    if not fields:
        fields.append(field("structure_needs_at_least_one_member", "uint8",
                            "Jazzy rosidl adds one placeholder octet for this empty component. Its default value is zero."))
    return tuple(fields), tuple(constants)


def service_event(service, source):
    return Record(service + "_Event", (
        field("info", "service_msgs/msg/ServiceEventInfo", "Middleware event type, timestamp, client identifier and sequence number."),
        Field("request", service + "_Request", "bounded", 1, doc="Zero or one request captured for this event."),
        Field("response", service + "_Response", "bounded", 1, doc="Zero or one response captured for this event."),
    ), (), source, True)


def action_envelopes(action, source):
    goal_id = field("goal_id", "unique_identifier_msgs/msg/UUID", "UUID identifying the action goal.")
    send = action + "_SendGoal"
    result = action + "_GetResult"
    def derived(name, *fields):
        return Record(name, tuple(fields), (), source, True)
    return [
        derived(send + "_Request", goal_id, field("goal", action + "_Goal", "Action-specific goal payload.")),
        derived(send + "_Response", field("accepted", "bool", "Whether the server accepted the goal."),
                field("stamp", "builtin_interfaces/msg/Time", "Time at which the server accepted the goal.")),
        service_event(send, source),
        derived(result + "_Request", goal_id),
        derived(result + "_Response", field("status", "int8", "Action protocol status from action_msgs/msg/GoalStatus."),
                field("result", action + "_Result", "Action-specific result payload.")),
        service_event(result, source),
        derived(action + "_FeedbackMessage", goal_id, field("feedback", action + "_Feedback", "Action-specific feedback for this goal.")),
    ]


def read_records():
    manifest = json.loads((UPSTREAM / "sources.json").read_bytes())
    notes = json.loads((HERE / "field_notes.json").read_bytes())
    errors = error_descriptions()
    records, inventories = {}, {}
    endings = {"msg": ("",), "srv": ("_Request", "_Response"), "action": ("_Goal", "_Result", "_Feedback")}
    for entry in manifest["files"]:
        path = UPSTREAM / entry["path"]
        data = path.read_bytes()
        if sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Upstream digest changed: {entry['path']}")
        if path.suffix[1:] not in endings:
            continue
        pkg, kind, _ = Path(entry["path"]).parts
        name = f"{pkg}/{kind}/{path.stem}"
        inventories.setdefault(pkg, []).append((kind, name))
        sections = re.split(r"(?m)^---[ \t]*\r?$", data.decode())
        for suffix, section in zip(endings[kind], sections, strict=True):
            key = name + suffix
            fields, constants = parse_section(pkg, section.splitlines(), notes, errors, key)
            records[key] = Record(key, fields, constants, entry["path"])
        derived = [service_event(name, entry["path"])] if kind == "srv" else action_envelopes(name, entry["path"]) if kind == "action" else []
        for rec in derived:
            records[rec.name] = rec
    for pkg, counts in VENDOR_COUNTS.items():
        actual = tuple(sum(k == kind for k, _ in inventories[pkg]) for kind in endings)
        if actual != counts:
            raise ValueError(f"Unexpected {pkg} inventory: {actual}")
        cmake = (UPSTREAM / pkg / "CMakeLists.txt").read_text()
        declared = re.findall(r'"((?:msg|srv|action)/\w+\.(?:msg|srv|action))"', cmake)
        frozen = [f"{name.removeprefix(pkg + '/')}.{kind}" for kind, name in inventories[pkg]]
        if sorted(declared) != sorted(frozen):
            raise ValueError(f"Interfaces disagree with {pkg}/CMakeLists.txt")
    ordered = {}
    def visit(key):
        rec = records[key]
        for f in rec.fields:
            if f.base not in PRIMITIVES and f.base not in ordered:
                visit(f.base)
        ordered[key] = rec
    for key in sorted(records):
        if key not in ordered:
            visit(key)
    return ordered


def traits(records):
    @cache
    def minimum(key):
        if key in PRIMITIVES:
            return PRIMITIVES[key]
        return sum(4 if f.form in ("bounded", "sequence") else
                   (f.count if f.form == "fixed" else 1) * minimum(f.base) for f in records[key].fields)
    @cache
    def borrows(key):
        if key in PRIMITIVES:
            return key == "string"
        return any(f.form in ("bounded", "sequence") or borrows(f.base) for f in records[key].fields)
    return minimum, borrows
