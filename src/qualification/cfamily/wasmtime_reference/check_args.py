#!/usr/bin/env python3
"""Exercise the qualification host's argument ABI with private wasm32 and wasm64 guests."""
import argparse
import ctypes
from pathlib import Path
import subprocess


# Seven UTF-8 bytes plus the terminating NUL fit one Wasm i64.load.
ARGV0 = "/p=é42"


class ByteVector(ctypes.Structure):
    _fields_ = [("size", ctypes.c_size_t), ("data", ctypes.c_void_p)]


def load_wasmtime(path):
    api = ctypes.CDLL(str(path.resolve(strict=True)))
    vector = ctypes.POINTER(ByteVector)
    api.wasmtime_wat2wasm.argtypes = [ctypes.c_char_p, ctypes.c_size_t, vector]
    api.wasmtime_wat2wasm.restype = ctypes.c_void_p
    api.wasmtime_error_message.argtypes = [ctypes.c_void_p, vector]
    api.wasmtime_error_message.restype = None
    api.wasmtime_error_delete.argtypes = [ctypes.c_void_p]
    api.wasmtime_error_delete.restype = None
    api.wasm_byte_vec_delete.argtypes = [vector]
    api.wasm_byte_vec_delete.restype = None
    return api


def assemble(api, wat):
    source = wat.read_bytes()
    binary = ByteVector()
    error = api.wasmtime_wat2wasm(source, len(source), ctypes.byref(binary))
    if error:
        message = ByteVector()
        api.wasmtime_error_message(error, ctypes.byref(message))
        try:
            detail = ctypes.string_at(message.data, message.size).decode("utf-8", errors="replace")
        finally:
            api.wasm_byte_vec_delete(ctypes.byref(message))
            api.wasmtime_error_delete(error)
        raise ValueError(f"{wat}: {detail}")
    try:
        return ctypes.string_at(binary.data, binary.size)
    finally:
        api.wasm_byte_vec_delete(ctypes.byref(binary))


def guest(bits, permitted):
    word = f"i{bits}"
    suffix = "_wasm64" if bits == 64 else ""
    address_type = "i64 " if bits == 64 else ""
    outside = 1 << 32 if bits == 64 else 65536

    def check_call(name, first, second, errno):
        return (f"(call $check (i32.eq (call {name} ({word}.const {first}) ({word}.const {second})) "
                f"(i32.const {errno})))")

    def check_word(address, value):
        return f"(call $check ({word}.eq ({word}.load ({word}.const {address})) ({word}.const {value})))"

    if permitted:
        payload = ARGV0.encode("utf-8") + b"\0"
        following = 16 + bits // 8
        body = f"""
      ({word}.store ({word}.const 0) ({word}.const -1))
      ({word}.store ({word}.const 8) ({word}.const -1))
      ({word}.store ({word}.const 16) ({word}.const -1))
      ({word}.store ({word}.const {following}) ({word}.const -1))
      (i64.store ({word}.const 65) (i64.const -1))
      (i32.store8 ({word}.const 73) (i32.const 90))
      {check_call("$sizes", 0, outside, 21)}
      {check_call("$sizes", 0, 9, 28)}
      {check_word(0, -1)}
      {check_call("$get", 16, 65529, 21)}
      {check_word(16, -1)}
      {check_call("$get", outside, 65, 21)}
      {check_call("$get", 17, 65, 28)}
      (call $check (i64.eq (i64.load ({word}.const 65)) (i64.const -1)))
      {check_call("$sizes", 0, 8, 0)}
      {check_word(0, 1)}
      {check_word(8, len(payload))}
      {check_call("$get", 16, 65, 0)}
      {check_word(16, 65)}
      {check_word(following, -1)}
      (call $check (i64.eq (i64.load ({word}.const 65)) (i64.const {int.from_bytes(payload, "little")})))
      (call $check (i32.eq (i32.load8_u ({word}.const 73)) (i32.const 90)))"""
    else:
        # An inaccessible output address must still yield the capability errno.
        body = check_call("$sizes", outside, outside, 76) + "\n" + check_call("$get", outside, outside, 76)
    return f"""(module
    (import "wasi_snapshot_preview1" "args_sizes_get{suffix}" (func $sizes (param {word} {word}) (result i32)))
    (import "wasi_snapshot_preview1" "args_get{suffix}" (func $get (param {word} {word}) (result i32)))
    (memory (export "memory") {address_type}1)
    (func $check (param $ok i32) (if (i32.eqz (local.get $ok)) (then unreachable)))
    (func (export "_start") {body}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True, help="qualification host executable")
    parser.add_argument("--wasmtime-lib", type=Path, required=True,
                        help="shared library from the verified Wasmtime 42.0.1 C API archive")
    parser.add_argument("--work", type=Path, required=True, help="empty output directory")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if any(args.work.iterdir()):
        parser.error("use an empty --work directory")
    api = load_wasmtime(args.wasmtime_lib)
    for bits in (32, 64):
        suffix = "_wasm64" if bits == 64 else ""
        for permitted in (True, False):
            stem = f"wasm{bits}-" + ("granted" if permitted else "denied")
            wat, wasm = (args.work / (stem + ext) for ext in (".wat", ".wasm"))
            wat.write_text(guest(bits, permitted), encoding="utf-8")
            wasm.write_bytes(assemble(api, wat))
            grant = ["grant=args", "guest-argv0=" + ARGV0]
            for mode, inputs in ([("allow", grant)] if permitted else [("allow", []), ("deny", grant)]):
                report = args.work / f"{stem}-{mode}.log"
                options = [f"{mode}={name}{suffix}" for name in ("args_get", "args_sizes_get")]
                subprocess.run([args.host, str(bits), "noeh", wasm, "-", report, *options, *inputs], check=True)
                if report.read_text().splitlines()[-1:] != ["end returned 0"]:
                    raise ValueError(f"guest did not return normally: {report}")


if __name__ == "__main__":
    main()
