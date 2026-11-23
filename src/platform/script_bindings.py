"""Emit typed read-only platform projections for QuickJS, TypeScript and bounded AssemblyScript."""
from model import octets


def es_module(record, *, declarations=False):
    lines = [f"/** Read-only projections of {record.spec['type']}. */"]
    if not declarations:
        lines += ['import { project } from "../../shared/reader.mjs";', "", "const fields = ["]
        for field in record.fields:
            lines.append(f'    ["{field.type}", {field.repeat}, {field.kind}], // {field.name}')
        lines += ["];", ""]
    for name, value in record.spec.get("constants", {}).items():
        lines.append(f"export declare const {name}: {value};" if declarations else f"export const {name} = {value};")
    for r in record.readings:
        lines += [f"/** Read {r.field.name} from the complete record. Invalid data or an invalid index returns undefined. */"]
        if declarations:
            result = {"i64": "bigint", "u64": "bigint", "bool": "boolean"}.get(r.field.type, "number")
            index = ", index: number" if r.indexed else ""
            lines.append(f"export declare function read_{r.name}(data: Uint8Array{index}): {result} | undefined;")
        else:
            index = ", index" if r.indexed else ""
            actual = "index" if r.indexed else "0"
            lines.append(f"export function read_{r.name}(data{index}) {{")
            if r.step != 1:
                lines.append("    if (!Number.isSafeInteger(index) || index < 0) return undefined;")
                actual = f"index * {r.step} + {r.base}"
            lines += [f"    return project(data, {record.mode}, fields, {r.number}, {actual});", "}"]
        lines.append("")
    return "\n".join(lines)


def literal(r, *, js=False):
    if r.field.type == "bool":
        return "true" if r.sample else "false"
    return str(r.sample) + ("n" if js and r.field.type in ("i64", "u64") else "")


def es_example(record, *, typed=False):
    lines = [f'import * as observation from "uwrosv2/platform/{record.platform}/observation";', "",
             "/* Constructed from the pinned upstream wire definition. */",
             "const sample = new Uint8Array([", octets(record.example()), "]);", ""]
    if record.mode in (1, 3):
        lines += ["const bigEndian = new Uint8Array([", octets(record.example(big_cdr=True)), "]);", ""]
    lines.append("function check(data" + (": Uint8Array): void {" if typed else ") {"))
    for r in record.readings:
        args = ", 1" if r.indexed else ""
        call = f"observation.read_{r.name}"
        lines += [f"    if ({call}(data{args}) !== {literal(r, js=True)}) throw Error(\"{r.name}\");",
                  f"    if ({call}(data.subarray(0, data.length - 1){args}) !== undefined) throw Error(\"truncated {r.name}\");"]
        if r.indexed:
            lines.append(f"    if ({call}(data, -1) !== undefined) throw Error(\"invalid index\");")
    lines += ["}", "", "check(sample);"]
    if record.mode in (1, 3):
        lines.append("check(bigEndian);")
    if record.mode == 3:
        lines.append("check(sample.subarray(4));")
    return "\n".join([*lines, ""])


def as_module(record):
    lines = [f"/** Read-only projections of {record.spec['type']} over bounded staging. */",
             'import { begin, field, finish, bits } from "../../shared/reader";', ""]
    for name, value in record.spec.get("constants", {}).items():
        lines.append(f"export const {name}: i32 = {value};")
    lines += ["function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {",
              f"    if (!begin({record.mode}, size, fromReply)) return false;"]
    for i, f in enumerate(record.fields):
        lines.append(f"    if (!field({f.width}, {f.repeat}, {f.kind}, wanted == {i}, index)) return false; // {f.name}")
    lines += ["    return finish();", "}", ""]
    for r in record.readings:
        t = r.field.type
        initial = "false" if t == "bool" else "0"
        index_param = ", index: u32" if r.indexed else ""
        actual = "index" if r.indexed else "0"
        lines += [f"/** Last successfully decoded {r.field.name}. */", f"export let {r.name}: {t} = {initial};", "",
                  f"/** Validate the complete request or reply span, then publish {r.name}. */",
                  f"export function read_{r.name}(size: u32{index_param}, fromReply: bool = false): bool {{"]
        if r.step != 1:
            limit = ((1 << 32) - 1 - r.base) // r.step
            lines.append(f"    if (index > {limit}) return false;")
            actual = f"index * {r.step} + {r.base}"
        value = {"f32": "reinterpret<f32>(<u32>bits)", "f64": "reinterpret<f64>(bits)",
                 "bool": "bits != 0"}.get(t, f"<{t}>bits")
        lines += [f"    if (!project(size, {r.number}, {actual}, fromReply)) return false;",
                  f"    {r.name} = {value};", "    return true;", "}", ""]
    return "\n".join(lines)


def as_example(record):
    lines = [f'import * as observation from "./uwrosv2/platform/{record.platform}/observation";',
             'import { writeByte, writeWord } from "./wros";', "", "function check(size: u32): void {"]
    for r in record.readings:
        idx = ", 1" if r.indexed else ""
        call = f"observation.read_{r.name}"
        lines += [f"    if (!{call}(size{idx}) || observation.{r.name} != {literal(r)}) unreachable();",
                  f"    if ({call}(size - 1{idx})) unreachable();"]
        if r.indexed:
            lines.append(f"    if ({call}(size, u32.MAX_VALUE)) unreachable();")
    lines += ["}", "", "/** Stage complete wire examples for the pinned upstream field layout. */",
              "export function _start(): void {"]
    samples = [record.example()]
    if record.mode in (1, 3):
        samples.append(record.example(big_cdr=True))
    if record.mode == 3:
        samples.append(record.example()[4:])
    for sample in samples:
        for start in range(0, len(sample), 8):
            chunk = sample[start:start + 8]
            if len(chunk) == 8:
                lines.append(f"    writeWord({start}, 0x{int.from_bytes(chunk, 'little'):016x});")
            else:
                lines.extend(f"    writeByte({start + i}, {value});" for i, value in enumerate(chunk))
        lines.append(f"    check({len(sample)});")
    return "\n".join([*lines, "}", ""])
