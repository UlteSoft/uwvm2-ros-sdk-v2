"""Render standalone Core WebAssembly text for a real, bounded platform reader."""
from pathlib import Path
import struct

from model import PACK

COMMON = Path(__file__).with_name("wat_reader.inc")


def project(record):
    lines = [
        "  (func $obs_project (param $p i32) (param $length i32) (param $wanted i32) (param $index i32)",
        "    (result i32 i64)",
        "    (local $size i64) (local $pos i64) (local $cdr i32) (local $big i32) (local $tail i64)",
        "    (local $saved i64) (local $v i64) (local $hit i32) (local $bits i64) (local $found i32)",
        "    (local.set $size (i64.extend_i32_u (local.get $length)))",
        "    (block $bad",
    ]
    if record.mode in (1, 3):
        condition = "(i32.const 1)" if record.mode == 1 else "(i32.ne (local.get $length) (i32.const 32))"
        lines.extend([
            f"      (local.set $cdr {condition})",
            "      (if (local.get $cdr) (then",
            "        (br_if $bad (i32.lt_u (local.get $length) (i32.const 4)))",
            "        (br_if $bad (i32.load8_u (local.get $p)))",
            "        (br_if $bad (i32.gt_u (i32.load8_u offset=1 (local.get $p)) (i32.const 1)))",
            "        (br_if $bad (i32.load8_u offset=2 (local.get $p)))",
            "        (local.set $tail (i64.load8_u offset=3 (local.get $p)))",
            "        (br_if $bad (i64.gt_u (local.get $tail) (i64.const 3)))",
            "        (local.set $big (i32.eqz (i32.load8_u offset=1 (local.get $p))))",
            "        (local.set $size (i64.sub (local.get $size) (i64.const 4)))",
            "        (local.set $p (i32.add (local.get $p) (i32.const 4)))))",
        ])
    if record.mode == 2:
        lines += [
            "      (br_if $bad (i32.lt_u (local.get $length) (i32.const 8)))",
            "      (br_if $bad (i64.ne (call $obs_word (local.get $p) (i64.const 0) (i32.const 8) (i32.const 1))",
            "                          (i64.const 0x4abec52f17edd11f)))",
            "      (local.set $big (i32.const 1))",
            "      (local.set $p (i32.add (local.get $p) (i32.const 8)))",
            "      (local.set $size (i64.sub (local.get $size) (i64.const 8)))",
        ]
    for j, f in enumerate(record.fields):
        lines += [
            f"      ;; {f.name}",
            "      (call $obs_field (local.get $p) (local.get $size) (local.get $pos)",
            f"        (i32.const {f.width}) (i32.const {f.repeat}) (i32.const {f.kind}) (local.get $saved)",
            f"        (local.get $cdr) (local.get $big) (i32.eq (local.get $wanted) (i32.const {j})) (local.get $index))",
            "      (local.set $hit) (local.set $v) (local.set $saved) (local.set $pos)",
            "      (br_if $bad (i64.lt_s (local.get $pos) (i64.const 0)))",
            "      (if (local.get $hit) (then (local.set $found (i32.const 1)) (local.set $bits (local.get $v))))",
        ]
    lines += [
        "      (br_if $bad (i32.eqz (local.get $found)))",
        "      (if (i64.ne (local.get $size) (local.get $pos)) (then",
        "        (br_if $bad (i64.ne (i64.sub (local.get $size) (local.get $pos)) (local.get $tail)))))",
        "      (if (i64.ne (local.get $tail) (i64.const 0)) (then",
        "        (br_if $bad (i64.ne (local.get $tail) (i64.and (i64.sub (i64.const 0) (local.get $pos)) (i64.const 3))))))",
        "      (return (i32.const 1) (local.get $bits)))",
        "    (i32.const 0) (i64.const 0))",
    ]
    return "\n".join(lines)


def accessors(record):
    lines = []
    stores = {1: "i64.store8", 2: "i64.store16", 4: "i64.store32", 8: "i64.store"}
    for r in record.readings:
        ip = " (param $index i32)" if r.indexed else ""
        lines += [f'  (func $read_{r.name} (export "read_{r.name}") (param $p i32) (param $size i32){ip} (param $out i32) (result i32)',
                  "    (local $ok i32) (local $bits i64)"]
        idx = "(local.get $index)" if r.indexed else "(i32.const 0)"
        if r.step != 1:
            limit = ((1 << 32) - 1 - r.base) // r.step
            lines += [f"    (if (i32.gt_u (local.get $index) (i32.const {limit})) (then (return (i32.const 0))))"]
            idx = f"(i32.add (i32.mul (local.get $index) (i32.const {r.step})) (i32.const {r.base}))"
        lines += [f"    (call $obs_project (local.get $p) (local.get $size) (i32.const {r.number}) {idx})",
                  "    (local.set $bits) (local.set $ok)",
                  f"    (if (local.get $ok) (then ({stores[r.field.width]} (local.get $out) (local.get $bits))))",
                  "    (local.get $ok))", ""]
    return "\n".join(lines)


def fixture_calls(record, data):
    lines = []
    for i in range(0, len(data), 8):
        chunk = data[i:i + 8]
        if len(chunk) == 8:
            lines.append(f"    (i64.store offset={i} (local.get $p) (i64.const 0x{int.from_bytes(chunk, 'little'):016x}))")
        else:
            for j, byte in enumerate(chunk):
                lines.append(f"    (i32.store8 offset={i+j} (local.get $p) (i32.const {byte}))")
    for r in record.readings:
        width = r.field.width
        raw = int.from_bytes(struct.pack("<" + PACK[r.field.type], r.sample), "little")
        load = "i64.load" + {8: "", 4: "32_u", 2: "16_u", 1: "8_u"}[width]
        index = " (i32.const 1)" if r.indexed else ""
        args = f"(local.get $p) (i32.const {len(data)}){index} (local.get $out)"
        short = f"(local.get $p) (i32.const {len(data)-1}){index} (local.get $out)"
        lines += [f"    (if (i32.eqz (call $read_{r.name} {args})) (then unreachable))",
                  f"    (if (i64.ne ({load} (local.get $out)) (i64.const 0x{raw:x})) (then unreachable))",
                  f"    (if (call $read_{r.name} {short}) (then unreachable))"]
        if r.indexed:
            lines += [f"    (if (call $read_{r.name} (local.get $p) (i32.const {len(data)}) (i32.const -1) (local.get $out)) (then unreachable))"]
    return lines


def wat_module(record, *, example):
    lines = [f";; Read-only {record.spec['type']}.", "(module", '  (memory $private (export "memory") 1)',
             COMMON.read_text().rstrip(), project(record), accessors(record)]
    if example:
        data = record.example()
        out_offset = (len(data) + 15) & ~15
        length = out_offset + 16
        lines += ['  (func (export "_start")', "    (local $p i32) (local $out i32)",
                  f"    (local.set $p (memtag.claim $private (i32.const 256) (i32.const {length})))",
                  f"    (local.set $out (i32.add (local.get $p) (i32.const {out_offset})))",
                  *fixture_calls(record, data)]
        if record.mode in (1, 3):
            lines.extend(fixture_calls(record, record.example(big_cdr=True)))
        if record.mode == 3:
            lines.extend(fixture_calls(record, data[4:]))
        lines.append(f"    (drop (memtag.release $private (local.get $p) (i32.const {length}))))")
    return "\n".join([*lines, ")", ""])
