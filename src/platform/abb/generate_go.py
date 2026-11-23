"""Generate Go ROS 1 domain packages from the same records and MD5s as C, C++ and Rust."""
import json
from collections import defaultdict
import subprocess
import textwrap

from generate_ros1 import PUBLIC, license_notice, minimum_sizes
from ros1_schema import PRIMITIVES, fingerprints, load


DESTINATION = PUBLIC / "go/ros1"
MODULE = "github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1"
DOMAINS = {
    "std_msgs": "provides the sequence number, timestamp and frame of an ABB ROS 1 status message.",
    "abb_egm_msgs": "reports Externally Guided Motion channel state and stamped channel arrays.",
    "abb_rapid_msgs": "represents RAPID positions, orientations, joint targets, loads, tools and work objects.",
    "abb_rapid_sm_addin_msgs": "represents RobotWare StateMachine Add-In settings, runtime state and four services.",
    "abb_robot_msgs": "provides robot controller state, RAPID symbol identification, service status and 18 RWS services.",
}
ACRONYMS = {word.lower(): word for word in ("ID", "EGM", "RAPID", "RC", "IO", "LP", "SG", "SM", "UC")}
WIRE = {"bool": "Bool", "uint8": "Uint8", "uint16": "Uint16", "uint32": "Uint32", "float32": "Float32",
        "float64": "Float64", "string": "String", "time": "Time"}


def identifier(name):
    return "".join(ACRONYMS.get(word, word.capitalize()) for word in name.lower().split("_"))


def go_package(package):
    return package.replace("_", "")


def go_type(type_name, package):
    if type_name in PRIMITIVES:
        return "ros1.Time" if type_name == "time" else type_name
    domain, name = type_name.split("/")
    return name if domain == package else go_package(domain) + "." + name


def docs(description, indent=""):
    lines = []
    for paragraph in description.split("\n\n"):
        if lines:
            lines.append(indent + "//")
        for line in textwrap.wrap(paragraph, width=90 - len(indent), break_long_words=False, break_on_hyphens=False):
            lines.append(indent + "// " + line)
    return lines


def record_code(record, hashes, minimum):
    name = record.name
    owner = record.service or name
    datatype = record.package + "/" + owner
    lines = []
    if not record.service or name == owner + "Request":
        lines += [f"// {owner}Type is the ROS 1 connection-header type.",
                  f'const {owner}Type = "{datatype}"',
                  f"// {owner}MD5 is the ROS 1 connection-header fingerprint.",
                  f'const {owner}MD5 = "{hashes[datatype]}"', ""]
    for const in record.constants:
        symbol = name + identifier(const.name)
        literal = json.dumps(const.value) if const.type == "string" else const.value
        lines.extend(docs(f"{symbol} is {record.qualified}.{const.name}. " + const.description))
        lines += [f"const {symbol} {const.type} = {literal}", ""]
    role = "request body" if name.endswith("Request") else "successful response body"
    description = (f"{name} is the {role} of {datatype}." if record.service
                   else f"{name} represents the ROS 1 message {datatype}.")
    if not record.fields:
        description += " Its body occupies zero bytes."
    lines.extend(docs(description + "\n\n" + record.description))
    lines.append(f"type {name} struct {{")
    for field in record.fields:
        typ = ("[]" if field.array else "") + go_type(field.type, record.package)
        lines.extend(docs(field.description, "\t"))
        lines.append(f'\t{identifier(field.name)} {typ} `ros:"{field.name}" json:"{field.name}"`')
    lines += ["}", "",
              f"// {name}MinSize is the body's byte count with empty strings and sequences.",
              f"const {name}MinSize = {minimum[record.qualified]}", "",
              "// ROS1Type returns the message or service type used in the connection header.",
              f"func (*{name}) ROS1Type() string {{ return {owner}Type }}", "",
              "// ROS1MD5 returns the message or service fingerprint used in the connection header.",
              f"func (*{name}) ROS1MD5() string {{ return {owner}MD5 }}", "",
              "// ROS1Fields visits this record's fields in wire order.",
              f"func (v *{name}) ROS1Fields(s *ros1.Stream) {{"]
    for field in record.fields:
        member = "v." + identifier(field.name)
        if field.array:
            if field.type in PRIMITIVES or minimum[field.type] < 1:
                raise ValueError("unsupported ABB sequence element " + field.type)
            element = go_type(field.type, record.package)
            lines.append(f"\tros1.Sequence(s, &{member}, {element}MinSize, (*{element}).ROS1Fields)")
        elif field.type in WIRE:
            lines.append(f"\ts.{WIRE[field.type]}(&{member})")
        else:
            lines.append(f"\t{member}.ROS1Fields(s)")
    lines += ["}", "",
              "// ROS1Size returns the exact encoded byte count.",
              f"func (v *{name}) ROS1Size() (int, error) {{ return ros1.Size(v, (*{name}).ROS1Fields) }}", "",
              "// MarshalROS1 writes a complete body into dst and returns the byte count.",
              "// A short buffer or invalid length leaves dst untouched.",
              f"func (v *{name}) MarshalROS1(dst []byte) (int, error) {{",
              f"\treturn ros1.MarshalTo(v, dst, (*{name}).ROS1Fields)", "}", "",
              "// UnmarshalROS1 decodes exactly one complete body into v. On error v is unchanged.",
              f"func (v *{name}) UnmarshalROS1(src []byte) error {{",
              f"\treturn ros1.Unmarshal(src, v, (*{name}).ROS1Fields)", "}", "",
              "// MarshalBinary implements encoding.BinaryMarshaler and allocates the result.",
              f"func (v *{name}) MarshalBinary() ([]byte, error) {{ return ros1.Marshal(v, (*{name}).ROS1Fields) }}", "",
              "// UnmarshalBinary implements encoding.BinaryUnmarshaler using ROS 1 body encoding.",
              f"func (v *{name}) UnmarshalBinary(src []byte) error {{ return v.UnmarshalROS1(src) }}", ""]
    return lines


def generate(package, records, hashes, minimum):
    domains = {f.type.split("/")[0] for rec in records for f in rec.fields if f.type not in PRIMITIVES}
    imports = [MODULE, *(MODULE + "/" + go_package(p) for p in sorted(domains - {package}))]
    pkg = go_package(package)
    lines = ["// Code generated by src/platform/abb/generate_go.py from pinned ROS 1 interfaces. DO NOT EDIT.",
             license_notice(), "", *docs(f"Package {pkg} " + DOMAINS[package]), f"package {pkg}", "", "import ("]
    lines.extend(f'\t"{path}"' for path in imports)
    lines.extend([")", ""])
    for rec in records:
        lines.extend(record_code(rec, hashes, minimum))
    return subprocess.check_output(["gofmt"], input="\n".join(lines).encode())


def main():
    records = load()
    hashes, minimum = fingerprints(records), minimum_sizes(records)
    groups = defaultdict(list)
    for rec in records:
        groups[rec.package].append(rec)
    for package, members in groups.items():
        target = DESTINATION / go_package(package) / "records.go"
        target.parent.mkdir(parents=True, exist_ok=True)
        data = generate(package, members, hashes, minimum)
        if not target.is_file() or target.read_bytes() != data:
            target.write_bytes(data)


if __name__ == "__main__":
    main()
