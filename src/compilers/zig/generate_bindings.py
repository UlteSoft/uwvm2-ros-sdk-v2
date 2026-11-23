"""Render the Zig imports and the eight local dashboard codecs from the pinned inputs."""
import json
from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/abi"))
sys.path.insert(0, str(ROOT / "src/platform/universal_robots"))
from language_contract import authority, domains, memory_contract, parameters, result_text
from generate_cdr import read_inputs

BASE = ROOT / "include/u2rosv2/universal/zig"
UR = ROOT / "include/u2rosv2/platform/universal_robots/zig"
TYPES = {"int8": "i8", "uint8": "u8", "uint32": "u32", "uint64": "u64", "string": "[]const u8"}


def doc(lines, text):
    for line in textwrap.wrap(text, 100, break_long_words=False, break_on_hyphens=False):
        lines.append("/// " + line)


def imports():
    contract = json.loads((ROOT / "src/abi/contract.json").read_bytes())
    root = ["//! Zig bindings for the registered ROSv2 scene operations.",
            "//! Pass guest addresses through `address` and use the contract's byte lengths on both pointer widths.",
            "", "/// Convert a guest pointer to the i64 carrier, including its WasmMTE tag.",
            "pub inline fn address(pointer: anytype) u64 {", "    return @intFromPtr(pointer);", "}",
            "", "/// Status codes returned by scene operations other than ABI discovery.", "pub const Status = struct {"]
    for name, value in contract["statuses"].items():
        root.append(f"    pub const {name}: u32 = {value};")
    root.extend(["};", ""])
    domain_dir = BASE / "domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    for domain, rows in domains(contract).items():
        root.extend([f"/// Registered operations in the `{domain}` domain.",
                     f'pub const {domain} = @import("domains/{domain}.zig");'])
        lines = [f"//! ROSv2 {domain} imports generated from src/abi/contract.json.", "", "const raw = struct {"]
        for row in rows:
            args = ", ".join(f"{p['name']}: u{p['type'][1:]}" for p in row["parameters"])
            lines.append(f'    extern "{contract["module"]}" fn @"{row["name"]}"({args}) u32;')
        lines.extend(["};", ""])
        for row in rows:
            name = row["name"]
            prefix = {"module_call": "module.call", "modules": "module", "types": "type"}.get(domain, domain)
            local_name = name.removeprefix(prefix + ".").replace(".", "_")
            doc(lines, name + ". " + row["contract"].strip())
            doc(lines, authority(row))
            doc(lines, memory_contract(row))
            for arg, description in parameters(row).items():
                doc(lines, f"`{arg}` — {description}")
            doc(lines, "Result. " + result_text(row))
            lines.extend([f'pub const {local_name} = raw.@"{name}";', ""])
        (domain_dir / (domain + ".zig")).write_text("\n".join(lines))
    (BASE / "root.zig").write_text("\n".join(root) + "\n")


def dashboard():
    messages, license_text = read_inputs()
    UR.mkdir(parents=True, exist_ok=True)
    (UR / "UPSTREAM-LICENSES.txt").write_text(license_text)
    lines = ["//! Message records generated from the dashboard package registered by the UR ROS 2 driver.",
             "//! Each string borrows its input bytes. The CDR codec accepts either byte order.",
             'const cdr = @import("cdr.zig");', "", "pub const Endian = cdr.Endian;",
             "pub const Error = cdr.Error;", ""]
    for msg in messages:
        lines.extend([f"/// `{msg.datatype}`.", f"/// Upstream definition at {msg.source}",
                      f"pub const {msg.name} = struct {{"])
        for kind, field, description in msg.fields:
            lines.extend(["    /// " + description, f"    {field}: {TYPES[kind]},"])
        lines.extend(["", "    /// Fully qualified ROS 2 type name.", f'    pub const ros_type = "{msg.datatype}";'])
        for kind, name, value in msg.constants:
            lines.extend([f"    /// Upstream `{kind}` constant `{name}`.",
                          f"    pub const {name}: {TYPES[kind]} = {json.dumps(value)};"])
        lines.extend(["", "    /// Decode one complete encapsulated message. Strings borrow the frame bytes.",
                      f"    pub fn decode(frame: []const u8) Error!{msg.name} {{",
                      f"        return cdr.decode({msg.name}, frame);", "    }", "",
                      "    /// Check the framing, field lengths, alignment and end of the message.",
                      "    pub fn validate(frame: []const u8) Error!void {",
                      "        _ = try decode(frame);", "    }", "",
                      "    /// Number of bytes needed for canonical framing, including the encapsulation.",
                      f"    pub fn encodedSize(self: {msg.name}) Error!usize {{",
                      "        return cdr.encodedSize(self);", "    }", "",
                      "    /// Encode in caller-owned storage. A short destination remains untouched.",
                      f"    pub fn encode(self: {msg.name}, order: Endian, out: []u8) Error!usize {{",
                      "        return cdr.encode(self, order, out);", "    }", "};", ""])
    (UR / "root.zig").write_text("\n".join(lines))
    frames = json.loads((ROOT / "src/platform/universal_robots/program_information_frames.json").read_bytes())
    lines = ["//! Hand-authored XCDRv1 interoperability fixtures from program_information_frames.json.", ""]
    for order in ("big", "little"):
        lines.append(f"pub const {order} = [_]u8{{")
        for line in frames[order]:
            lines.append("    " + ", ".join("0x" + b for b in line.split()) + ",")
        lines.extend(["};", ""])
    (ROOT / "src/examples/universal_robots/zig/frames.zig").write_text("\n".join(lines))


if __name__ == "__main__":
    imports()
    dashboard()
