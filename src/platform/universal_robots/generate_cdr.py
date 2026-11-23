"""Generate C, C++98 and no_std Rust records from the pinned dashboard .msg files."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = "ur_dashboard_msgs"
PUBLIC = ROOT / "include/u2rosv2/platform/universal_robots"
C_DIR = PUBLIC / "c/uwrosv2/universal_robots/cdr"
CPP_DIR = PUBLIC / "c++/uwrosv2/universal_robots/cdr"
RUST_DIR = PUBLIC / "rust/cdr"
TEMPLATES = HERE.parent / "franka"  # The two native framing templates are parameterized by prefix.
P = "uwrosv2_universal_robots_cdr_"
C_NX = "UWROSV2_UNIVERSAL_ROBOTS_CDR_C_NOEXCEPT"
CPP_NX = "UWROSV2_UNIVERSAL_ROBOTS_CDR_NOEXCEPT"
SCALARS = {"int8": ("int8_t", "i8", 1), "uint8": ("uint8_t", "u8", 1),
           "uint32": ("uint32_t", "u32", 4), "uint64": ("uint64_t", "u64", 8)}
FIELD_DOCS = {
    "OperationalMode": {"mode": "Dashboard operational mode, such as MANUAL or AUTOMATIC."},
    "ProgramInformation": {
        "name": "Program name returned by the dashboard.",
        "description": "Program description returned by the dashboard.",
        "created_date": "Creation date as the unsigned value supplied by the dashboard.",
        "last_saved_date": "Last save date as the unsigned value supplied by the dashboard.",
        "last_modified_date": "Last modification date as the unsigned value supplied by the dashboard.",
        "program_state": "Program revision state, such as DRAFT or FINAL.",
    },
    "ProgramState": {"state": "Execution state, such as STOPPED, PLAYING or PAUSED."},
    "RobotMode": {"mode": "Signed robot operating-mode code. NO_CONTROLLER is -1."},
    "SafetyMode": {"mode": "Unsigned safety-mode code reported by the dashboard."},
    "SafetyStatus": {"status": "Signed safety-status code reported by the dashboard."},
    "UserRole": {"role": "User role reported by the dashboard."},
    "VersionInformation": {"major": "PolyScope major version number.", "minor": "PolyScope minor version number.",
                           "bugfix": "PolyScope bugfix version number.", "build": "PolyScope build number."},
}


@dataclass(frozen=True)
class Message:
    name: str
    source: str
    fields: list
    constants: list

    @property
    def datatype(self):
        return f"{PACKAGE}/msg/{self.name}"


def parse_message(data, name, url):
    fields, constants = [], []
    for line in data.splitlines():
        declaration = line.partition("#")[0].strip()
        if not declaration:
            continue
        kind, member = declaration.split(None, 1)
        if kind not in SCALARS and kind != "string":
            raise ValueError(f"{name}: unsupported dashboard field type {kind}")
        field, assignment, value = (part.strip() for part in member.partition("="))
        if not assignment:
            fields.append((kind, field, FIELD_DOCS[name][field]))
        elif kind == "string":
            # The frozen .msg files use both bare words and double-quoted words.
            literal = value[1:-1] if value.startswith('"') and value.endswith('"') else value
            if not re.fullmatch(r"[A-Z_]+", literal):
                raise ValueError(f"{name}.{field}: unsupported string literal {value}")
            constants.append((kind, field, literal))
        else:
            constants.append((kind, field, int(value)))
    return Message(name, url, fields, constants)


def read_inputs():
    sources = json.loads((HERE / "upstream.json").read_bytes())
    package = next(entry for entry in sources if entry["package"] == PACKAGE)
    entries = {entry["file"]: entry for entry in package["files"]}

    def pinned(relative):
        data = (HERE / "upstream" / PACKAGE / relative).read_bytes()
        if sha256(data).hexdigest() != entries[relative]["sha256"]:
            raise ValueError(f"Digest mismatch for {PACKAGE}/{relative}")
        return data.decode()

    cmake = pinned("CMakeLists.txt")
    group = re.search(r"(?ms)^set\(msg_files\s+(.*?)\)", cmake)
    declared = set(group.group(1).split()) if group else set()
    frozen = {path for path in entries if path.endswith(".msg")}
    if not declared or declared != frozen:
        raise ValueError(f"{PACKAGE} message inventory differs from CMakeLists.txt")
    messages = []
    for relative in sorted(declared):
        url = f"{package['url']}/blob/{package['commit']}/{entries[relative]['source_path']}"
        messages.append(parse_message(pinned(relative), Path(relative).stem, url))
    notice = f"{PACKAGE} from {package['url']} at {package['commit']} ({package['license']}).\n\n"
    return messages, notice + pinned("LICENSE")


def save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def template(name, **values):
    content = (TEMPLATES / name).read_text().rstrip()
    for key, value in values.items():
        content = content.replace("@" + key + "@", value)
    return content


def guard(cpp, name):
    return f"UWROSV2_UNIVERSAL_ROBOTS_CDR_{name.upper()}_{'HPP' if cpp else 'H'}"


CPP_NAMESPACE = "namespace uwrosv2 { namespace universal_robots { namespace cdr {"
CPP_CLOSE = "} } } // namespace uwrosv2::universal_robots::cdr"
BANNER = "Generated by src/platform/universal_robots/generate_cdr.py. Upstream BSD notice in UPSTREAM-LICENSES.txt."


def wire(cpp):
    prefix = "" if cpp else P
    nx = CPP_NX if cpp else C_NX
    name = guard(cpp, "wire")
    lines = [f"/* {BANNER} */", f"#ifndef {name}", f"#define {name}", "#include <stddef.h>",
             "#include <stdint.h>", "#include <limits.h>", "#include <float.h>", "#include <string.h>", "",
             "#if defined(__cplusplus) && (__cplusplus >= 201103L || (defined(_MSVC_LANG) && _MSVC_LANG >= 201103L))",
             f"#define {nx} noexcept", "#elif defined(__cplusplus)", f"#define {nx} throw()",
             "#else", f"#define {nx}", "#endif", ""]
    if cpp:
        lines += [CPP_NAMESPACE, ""]
    lines += [template("native_wire.inc", p=prefix, NX=nx), ""]
    for kind, (native, _, width) in SCALARS.items():
        lines += [f"static inline int {prefix}get_{kind}({prefix}reader *r, {native} *out) {nx} {{",
                  "    uint64_t bits;", f"    if (!{prefix}get_word(r, {width}, &bits)) return 0;"]
        if kind == "int8":
            lines += ["    const uint8_t octet = (uint8_t)bits;", "    memcpy(out, &octet, sizeof octet);"]
        else:
            lines.append(f"    *out = ({native})bits;")
        lines += ["    return 1;", "}", "",
                  f"static inline int {prefix}put_{kind}({prefix}writer *w, const {native} *value) {nx} {{",
                  f"    return {prefix}put_word(w, {width}, (uint{width * 8}_t)*value);", "}", ""]
    if cpp:
        lines += [CPP_CLOSE]
    return "\n".join([*lines, "#endif", ""])


def native_type(kind, prefix):
    return prefix + "string" if kind == "string" else SCALARS[kind][0]


def transfer(message, cpp, read):
    action, cursor = ("get", "r") if read else ("put", "w")
    prefix = "" if cpp else P
    indent = "        " if cpp else "    "
    lines = [f"{indent}if (!{prefix}{action}_{kind}({cursor}, &v->{name})) return {'false' if cpp else '0'};"
             for kind, name, _ in message.fields]
    return [*lines, indent + ("return true;" if cpp else "return 1;")]


def native_record(message, cpp):
    t = message.name if cpp else P + PACKAGE + "_" + message.name
    prefix = "" if cpp else P
    nx = CPP_NX if cpp else C_NX
    lines = [f"namespace {PACKAGE} {{"] if cpp else []
    lines += [f"/** {message.datatype}.", f" * @see {message.source}", " */",
              f"struct {t} {{" if cpp else "typedef struct {"]
    for kind, name, description in message.fields:
        view = " Borrows content bytes after decoding." if kind == "string" else ""
        lines += [f"    /** {description}{view} */", f"    {native_type(kind, prefix)} {name};"]
    if cpp:
        lines += ["", f'    static const char *datatype() {nx} {{ return "{message.datatype}"; }}',
                  f"    static {t} defaults() {nx} {{ return {t}(); }}", "};", ""]
    else:
        lines += [f"}} {t};", f'#define {t}_DATATYPE "{message.datatype}"', "",
                  f"static inline {t} {t}_defaults(void) {nx} {{",
                  f"    {t} value = {{0}};", "    return value;", "}", ""]
    if message.constants:
        if cpp:
            lines.append(f"namespace {t}_Constants {{")
        lines.append("/** Named ROS constants for this message. These occupy no bytes in the frame. */")
        for kind, name, literal in message.constants:
            symbol = name if cpp else f"{t}_{name}"
            if kind == "string":
                quoted = json.dumps(literal)
                lines += [f"static const uint8_t {symbol}_bytes[] = {quoted};",
                          f"static const {prefix}string {symbol} =",
                          f"    {{{symbol}_bytes, sizeof({symbol}_bytes) - 1}};"]
            elif cpp:
                lines.append(f"static const {native_type(kind, prefix)} {symbol} = {literal};")
            else:
                lines.append(f"#define {symbol} (({native_type(kind, prefix)}){literal})")
        if cpp:
            lines.append(f"}} // namespace {t}_Constants")
        lines.append("")
    if cpp:
        qualified = PACKAGE + "::" + t
        lines += [f"}} // namespace {PACKAGE}", "", f"template<> struct value_codec<{qualified}> {{",
                  f"    static bool get(reader *r, {qualified} *v) {nx} {{", *transfer(message, True, True), "    }",
                  f"    static bool put(writer *w, const {qualified} *v) {nx} {{", *transfer(message, True, False),
                  "    }", "};", ""]
    else:
        lines += [f"static inline int {t}_get({P}reader *r, {t} *v) {nx} {{", *transfer(message, False, True), "}", "",
                  f"static inline int {t}_put({P}writer *w, const {t} *v) {nx} {{", *transfer(message, False, False),
                  "}", "", template("c_record_api.inc", p=P, t=t, NX=nx), ""]
    return lines


def rust_record(message):
    borrows = any(kind == "string" for kind, _, _ in message.fields)
    t = message.name + ("<'a>" if borrows else "")
    lines = [f"/// {message.datatype}. [Upstream definition]({message.source}).",
             "#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]", f"pub struct {t} {{"]
    for kind, name, description in message.fields:
        if kind == "string":
            description += " Borrows the input bytes before the terminal NUL."
        rust = "&'a [u8]" if kind == "string" else SCALARS[kind][1]
        lines += [f"    /// {description}", f"    pub {name}: {rust},"]
    lines += ["}", ""]
    if message.constants:
        constant_owner = message.name + ("<'_>" if borrows else "")
        lines.append(f"impl {constant_owner} {{")
        for kind, name, literal in message.constants:
            rust, value = ("&'static [u8]", "b" + json.dumps(literal)) if kind == "string" else (SCALARS[kind][1], literal)
            lines += [f"    /// Named value of {message.datatype}.", f"    pub const {name}: {rust} = {value};"]
        lines += ["}", ""]
    lines += [f"impl<'a> Message<'a> for {t} {{", f'    const TYPE: &\'static str = "{message.datatype}";',
              "    fn read(r: &mut Reader<'a>) -> Result<Self, Error> {", "        Ok(Self {"]
    for kind, name, _ in message.fields:
        member = "string" if kind == "string" else SCALARS[kind][1]
        lines.append(f"            {name}: r.{member}()?,")
    lines += ["        })", "    }", "    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> {"]
    for kind, name, _ in message.fields:
        member = "string" if kind == "string" else SCALARS[kind][1]
        lines.append(f"        w.{member}(self.{name})?;")
    return [*lines, "        Ok(())", "    }", "}", ""]


def example_frames():
    examples = ROOT / "src/examples/universal_robots"
    frames = json.loads((HERE / "program_information_frames.json").read_bytes())
    native = ["/* " + frames["origin"] + " */", "#ifndef UR_EXAMPLE_PROGRAM_INFORMATION_FRAMES_H",
              "#define UR_EXAMPLE_PROGRAM_INFORMATION_FRAMES_H", "#include <stdint.h>", ""]
    rust = ["// " + frames["origin"], ""]
    for order in ("big", "little"):
        name = "metadata_" + order
        # Keep the header, individually aligned fields and final string visible in the example.
        rows = ["    " + ", ".join(f"0x{byte:02x}" for byte in bytes.fromhex(row)) + "," for row in frames[order]]
        native += [f"static const uint8_t {name}[] = {{", *rows, "};", ""]
        rust += [f"pub const {name.upper()}: &[u8] = &[", *rows, "];", ""]
    for language in ("c", "cpp"):
        save(examples / language / "cdr/program_information_frames.h", "\n".join([*native, "#endif", ""]))
    save(examples / "rust/cdr/program_information_frames.rs", "\n".join(rust))


def main():
    messages, license_text = read_inputs()
    save(CPP_DIR / "codec.hpp", (HERE / "cpp_codec.hpp.in").read_text())
    save(RUST_DIR / "mod.rs", (HERE / "rust_cdr.rs.in").read_text())
    for cpp, directory, ext in [(False, C_DIR, "h"), (True, CPP_DIR, "hpp")]:
        save(directory / f"wire.{ext}", wire(cpp))
        name = guard(cpp, PACKAGE)
        lines = [f"/* {BANNER} */", f"#ifndef {name}", f"#define {name}",
                 '#include "codec.hpp"' if cpp else '#include "wire.h"', ""]
        if cpp:
            lines += [CPP_NAMESPACE, ""]
        for message in messages:
            lines += native_record(message, cpp)
        if cpp:
            lines += [CPP_CLOSE]
        save(directory / f"{PACKAGE}.{ext}", "\n".join([*lines, "#endif", ""]))
        name = guard(cpp, "records")
        save(directory / f"records.{ext}", "\n".join([f"#ifndef {name}", f"#define {name}",
                                                      f'#include "{PACKAGE}.{ext}"', "#endif", ""]))
    lines = [f"//! {BANNER}", "use super::{Error, Message, Reader, Writer};", ""]
    for message in messages:
        lines += rust_record(message)
    save(RUST_DIR / (PACKAGE + ".rs"), "\n".join(lines))
    for directory in [C_DIR, CPP_DIR, RUST_DIR]:
        save(directory / "UPSTREAM-LICENSES.txt", license_text)
    example_frames()

    # The standard observation generator registers this platform's Rust module and installed guides.
    sys.path.insert(0, str(HERE.parent))
    from generate import generate
    from model import Record
    spec = json.loads((HERE.parent / "observations.json").read_bytes())["universal_robots"]
    generate(Record("universal_robots", spec))


if __name__ == "__main__":
    main()
