"""Identify a prepared WebAssembly-only Flang or the explicit ABI validation producer."""
import json
from compiler import digest

LLVM_REVISION = "392dfff97d29b59d77e5cac6d4b6ef2585fe7117"
ABI_PATCH = {"path": "third-parties/fortran/llvm23-wasm-abi.patch",
             "sha256": "72f1bccd7366c2f624473f5418113e5275a4fa3762e08a013e1e98be1d144ff8"}
VALIDATION_FLANG = "4756550cedf51ed844b32436270d89ad73b590a3c13b504b3ac8db9935cc8702"


def identity(binary):
    return dict(format="wros-flang-wasm-producer", llvm_revision=LLVM_REVISION,
                patch_sha256=ABI_PATCH["sha256"], compiler_sha256=digest(binary),
                targets=["WebAssembly"])


def require_compiler(binary, explicitly_selected):
    expected = identity(binary)
    if explicitly_selected and expected["compiler_sha256"] == VALIDATION_FLANG:
        return
    record = binary.with_name(binary.name + ".json")
    if not record.is_file() or record.stat().st_size > 1024 or json.loads(record.read_bytes()) != expected:
        raise ValueError("unrecognized Flang; build the WebAssembly-only compiler with build_flang.py")
