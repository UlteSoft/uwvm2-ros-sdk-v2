"""Generate selected C, C++98-through-26, and no_std Rust observation interfaces."""
from model import C_TYPE, octets


def c_type(reading, cpp):
    return "bool" if cpp and reading.field.type == "bool" else C_TYPE[reading.field.type]


def c_header(record, cpp):
    p = record.ident
    upper = p.upper()
    guard = f"UWROSV2_{upper}_OBSERVATION_H" + ("PP" if cpp else "")
    lines = [f"/** Read-only projections of {record.spec['type']}. */", f"#ifndef {guard}", f"#define {guard}",
             '#include "../../../../shared/reader.h"', ""]
    name = "" if cpp else f"uwrosv2_{p}_"
    spec = f"{name}observation_layout"
    if cpp:
        lines += [f"namespace uwrosv2 {{ namespace {p} {{", ""]
    for key, value in record.spec.get("constants", {}).items():
        k = key.lower() if cpp else f"UWROSV2_{upper}_{key}"
        lines.append(f"enum {{ {k} = {value} }};")
    lines += [f"static const uwrosv2_obs_field {spec}[] = {{"]
    for f in record.fields:
        lines += [f"    {{{f.width}, {f.repeat}, {f.kind}}}, /* {f.name} */"]
    lines += ["};", ""]
    for r in record.readings:
        t = c_type(r, cpp)
        index_param = ", size_t index" if r.indexed else ""
        output = "&" if cpp else "*"
        out = "out" if cpp else "*out"
        lines += [f"/** Read {r.field.name}" + (" at a zero-based index" if r.indexed else "") + ". Commit the output on success. */",
                  f"static inline {'bool' if cpp else 'int'} {name}read_{r.name}(const uint8_t *data, size_t size{index_param}, {t} {output}out) UWROSV2_OBS_NOEXCEPT {{"]
        if not cpp:
            lines.append("    if (!out) return 0;")
        idx = "index" if r.indexed else "0"
        if r.step != 1:
            lines.append(f"    if (index > (SIZE_MAX - {r.base}u) / {r.step}u) return 0;")
            idx = f"index * {r.step}u + {r.base}u"
        lines += ["    uint64_t bits;",
                  f"    if (!uwrosv2_obs_project(data, size, {record.mode}, {spec},",
                  f"                            sizeof {spec} / sizeof {spec}[0], {r.number}, {idx}, &bits)) return 0;"]
        if r.field.type.startswith("f") or r.field.type.startswith("i"):
            w = r.field.width * 8
            lines += [f"    const uint{w}_t word = (uint{w}_t)bits;", "    memcpy(" + ("&out" if cpp else "out") + ", &word, sizeof word);"]
        elif r.field.type == "bool" and cpp:
            lines.append("    out = bits != 0;")
        else:
            lines.append(f"    {out} = ({t})bits;")
        lines += ["    return 1;", "}", ""]
    if cpp:
        lines += [f"}} }} // namespace uwrosv2::{p}", ""]
    return "\n".join([*lines, "#endif", ""])


def c_example(record, cpp):
    p = record.ident
    prefix = f"uwrosv2::{p}::" if cpp else f"uwrosv2_{p}_"
    suffix = "hpp" if cpp else "h"
    lines = [f"#include <uwrosv2/{p}/observation.{suffix}>", "",
             "/* Constructed from the pinned interface definition. */",
             "static const volatile uint8_t example[] = {", octets(record.example()), "};", ""]
    if record.mode in (1, 3):
        lines.extend(["static const volatile uint8_t big_endian[] = {", octets(record.example(big_cdr=True)), "};", ""])
    lines += [f"static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {{",
              "    uint8_t data[sizeof example];", "    for (size_t i = 0; i < size; ++i) data[i] = source[i];"]
    for r in record.readings:
        t = c_type(r, cpp)
        name = prefix + "read_" + r.name
        out = "actual" if cpp else "&actual"
        index = ", 1" if r.indexed else ""
        value = str(r.sample) + ("f" if r.field.type == "f32" else "")
        if r.field.type in ("u64", "i64"):
            if cpp:
                magnitude = abs(r.sample)
                word = f"((static_cast<uint64_t>({magnitude >> 32}u) << 32) | {magnitude & 0xffffffff}u)"
                value = word if r.field.type == "u64" else ("-" if r.sample < 0 else "") + f"static_cast<int64_t>({word})"
            else:
                value = ("UINT64_C" if r.field.type == "u64" else "INT64_C") + f"({r.sample})"
        lines += ["    {", f"        {t} actual = 0;",
                  f"        if (!{name}(data, size{index}, {out}) || actual != {value}) __builtin_trap();",
                  f"        if ({name}(data, size - 1{index}, {out}) || actual != {value}) __builtin_trap();"]
        if r.indexed:
            lines += [f"        if ({name}(data, size, SIZE_MAX, {out})) __builtin_trap();"]
        lines += ["    }"]
    lines.extend(["}", "", ('extern "C" ' if cpp else "") + "void _start(void) UWROSV2_OBS_NOEXCEPT {", "    check_frame(example, sizeof example);"])
    if record.mode in (1, 3):
        lines.append("    check_frame(big_endian, sizeof big_endian);")
    if record.mode == 3:
        lines.append("    check_frame(example + 4, sizeof example - 4);")
    return "\n".join([*lines, "}", ""])


def rust_header(record):
    lines = [f"//! Read-only projections of {record.spec['type']}.", "#![no_std]", '#[path = "../../shared/reader.rs"]',
             "mod reader;", "use reader::Field;", ""]
    for module in record.spec.get("wire_modules", []):
        lines.extend([f"pub mod {module};", ""])
    for name, value in record.spec.get("constants", {}).items():
        lines.append(f"pub const {name}: i32 = {value};")
    lines.extend(["const LAYOUT: &[Field] = &["])
    for f in record.fields:
        lines.append(f"    Field({f.width}, {f.repeat}, {f.kind}), // {f.name}")
    lines += ["];", ""]
    for r in record.readings:
        idx = "index" if r.indexed else "0"
        index_param = ", index: usize" if r.indexed else ""
        kind = r.field.type
        lines += [f"/// Read {r.field.name}" + (" at a zero-based index." if r.indexed else "."),
                  f"pub fn read_{r.name}(data: &[u8]{index_param}) -> Option<{kind}> {{"]
        if r.step != 1:
            lines.append(f"    let index = index.checked_mul({r.step})?.checked_add({r.base})?;")
        lines.append(f"    let bits = reader::project(data, {record.mode}, LAYOUT, {r.number}, {idx})?;")
        result = {"f32": "f32::from_bits(bits as u32)", "f64": "f64::from_bits(bits)", "bool": "bits != 0", "u64": "bits"}
        lines += [f"    Some({result.get(kind, 'bits as ' + kind)})", "}", ""]
    return "\n".join(lines)


def rust_example(record):
    lines = ["#![no_std]", '#[cfg(target_arch = "wasm32")]', "use core::arch::wasm32::unreachable;",
             '#[cfg(target_arch = "wasm64")]', "use wros_runtime::abort as unreachable;",
             "use core::{hint::black_box, panic::PanicInfo};",
             "use wros_observation::*;", "", "#[panic_handler]", "fn panic(_: &PanicInfo) -> ! { unreachable() }", "",
             "// Constructed wire examples for the pinned upstream definition.", "const EXAMPLE: &[u8] = &[",
             octets(record.example()), "];", ""]
    if record.mode in (1, 3):
        lines += ["const BIG_ENDIAN: &[u8] = &[", octets(record.example(big_cdr=True)), "];", ""]
    lines += ["fn check(data: &[u8]) {"]
    for r in record.readings:
        name = "read_" + r.name
        idx = ", 1" if r.indexed else ""
        value = str(r.sample)
        if r.field.type == "bool":
            value = "true" if r.sample else "false"
        lines += [f"    if {name}(data{idx}) != Some({value}) || {name}(&data[..data.len() - 1]{idx}).is_some() {{ unreachable() }}"]
        if r.indexed:
            lines.append(f"    if {name}(data, usize::MAX).is_some() {{ unreachable() }}")
    lines += ["}", "", "#[no_mangle]", 'pub extern "C" fn _start() {', "    check(black_box(EXAMPLE));"]
    if record.mode in (1, 3):
        lines.append("    check(black_box(BIG_ENDIAN));")
    if record.mode == 3:
        lines.append("    check(black_box(&EXAMPLE[4..]));")
    return "\n".join([*lines, "}", ""])
