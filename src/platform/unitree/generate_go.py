"""Generate the Unitree ROS 2 Go types and both fixed-layout LowState CDR codecs."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent / "upstream/ros2"
DEST = ROOT / "include/u2rosv2/platform/unitree/go"
MODULE = "github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree"
SCALAR = set("bool string float32 float64 int8 int16 int32 int64 uint8 uint16 uint32 uint64".split())
WIDTH = {"int8": 1, "uint8": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4, "float32": 4}
ACRONYMS = {s.lower(): s for s in ("ADC", "BMS", "CRC", "DQ", "DDQ", "ID", "IMU", "NTC", "RPY", "SDK",
                                         "SN", "SOC", "SOH", "UWB", "UUID", "BQ", "MCU", "API")}
HEADER = "// Code generated from Unitree ROS 2 v0.3.0 .msg files by generate_go.py. DO NOT EDIT."


def exported(s):
    return "".join(ACRONYMS.get(part, part[0].upper() + part[1:]) for part in s.split("_"))


def fields(path):
    result = []
    for line in path.read_text().splitlines():
        clean = line.partition("#")[0].strip()
        if not clean:
            continue
        m = re.fullmatch(r"(\w+)(?:\[(\d*)\])?\s+(\w+)", clean)
        if not m:
            raise ValueError(f"{path}: unsupported ROS field {clean!r}")
        kind, count, name = m.groups()
        result.append((kind, count, name))
    return result


def render_types(pkg, schemas):
    lines = [HEADER, "", f"// Package {pkg} maps the public {pkg.replace('unitree', 'unitree_')} message definitions to Go.",
             f"package {pkg}", ""]
    for name, rows in schemas.items():
        lines.extend([f"// {name} represents {pkg.replace('unitree', 'unitree_')}/msg/{name}.", f"type {name} struct {{"])
        for kind, count, field in rows:
            if kind not in SCALAR and kind not in schemas:
                raise ValueError(f"unresolved type {kind} in {name}")
            t = (f"[{count}]" if count is not None else "") + kind
            lines.append(f'\t{exported(field)} {t} `json:"{field}"`')
        lines.extend(["}", ""])
    return "\n".join(lines)


def low_state_codec(pkg, schemas):
    codecs = {}

    def visit(name, offset):
        lines = [f"func (m *{name}) cdr(s *xcdr1.Stream) {{"]
        for kind, count, field in schemas[name]:
            value = "m." + exported(field)
            repeat = int(count) if count is not None else 1
            if count is not None:
                lines.append(f"\tfor i := range {value} {{")
                value += "[i]"
            indent = "\t" if count is None else "\t\t"
            if kind in schemas:
                lines.append(f"{indent}{value}.cdr(s)")
                for _ in range(repeat):
                    offset = visit(kind, offset)
            else:
                width = WIDTH[kind]
                offset = (offset + width - 1) // width * width + repeat * width
                lines.append(f"{indent}s.{kind.capitalize()}(&{value})")
            if count is not None:
                lines.append("\t}")
        codecs[name] = "\n".join([*lines, "}", ""])
        return offset

    size = 4 + visit("LowState", 0)
    return f'''{HEADER}

package {pkg}

import (
	"encoding/binary"
	"{MODULE}/internal/xcdr1"
)

// LowStateCDRSize includes the four-byte plain CDR encapsulation header.
const LowStateCDRSize = {size}

// MarshalCDR writes one complete LowState in the selected byte order.
// It returns false for a nil receiver, short destination or unsupported byte order.
func (m *LowState) MarshalCDR(dst []byte, order binary.ByteOrder) bool {{
	if m == nil || len(dst) < LowStateCDRSize || (order != binary.LittleEndian && order != binary.BigEndian) {{
		return false
	}}
	dst = dst[:LowStateCDRSize]
	clear(dst)
	if order == binary.LittleEndian {{
		dst[1] = 1
	}}
	m.cdr(&xcdr1.Stream{{Body: dst[4:], Order: order}})
	return true
}}

// UnmarshalCDR decodes a complete CDR_BE or CDR_LE payload with zero
// encapsulation options. A rejected header or length leaves m untouched.
func (m *LowState) UnmarshalCDR(src []byte) bool {{
	if m == nil || len(src) != LowStateCDRSize || src[0] != 0 || src[1] > 1 || src[2] != 0 || src[3] != 0 {{
		return false
	}}
	var order binary.ByteOrder = binary.BigEndian
	if src[1] == 1 {{
		order = binary.LittleEndian
	}}
	m.cdr(&xcdr1.Stream{{Body: src[4:], Order: order, Read: true}})
	return true
}}

''' + "\n".join(codecs[name] for name in sorted(codecs))


def main():
    for path in sorted(SOURCE.glob("unitree_*")):
        pkg = path.name.replace("_", "")
        schemas = {p.stem: fields(p) for p in sorted((path / "msg").glob("*.msg"))}
        output = DEST / pkg
        output.mkdir(exist_ok=True)
        (output / "types.go").write_bytes(subprocess.check_output(["gofmt"], input=render_types(pkg, schemas).encode()))
        if "LowState" in schemas:
            (output / "low_state_cdr.go").write_bytes(subprocess.check_output(["gofmt"], input=low_state_codec(pkg, schemas).encode()))


if __name__ == "__main__":
    main()
