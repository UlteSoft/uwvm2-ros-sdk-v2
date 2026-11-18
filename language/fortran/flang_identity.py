"""Verify the source recipe and identity of the WebAssembly-only Flang producer."""
import hashlib
import json
from compiler import digest

LLVM_REVISION = "392dfff97d29b59d77e5cac6d4b6ef2585fe7117"
LLVM_RECIPE_SHA256 = "1e5f3492b5f042ddaa5ea52f4a8ab3cb26782742dc6ce5b2ca17cad5df7b66de"
ABI_PATCH = {"path": "third-parties/fortran/llvm23-wasm-abi.patch",
             "sha256": "72f1bccd7366c2f624473f5418113e5275a4fa3762e08a013e1e98be1d144ff8"}
GLOBALS_HEADER_PATCH = {"path": "third-parties/fortran/llvm23-globals-intrinsic-header.patch",
                       "sha256": "31a4c2be6a0e8dfa14eb48777d9678ccb55bdbad6312826f9c2e0b91d0c9be63"}
ASSUMED_EXTENT_PATCH = {"path": "third-parties/fortran/llvm23-flang-assumed-size-index.patch",
                       "sha256": "2f6cbd70a3ec9d742b9827d36133f1681f566378140afaa846022ef3921cf472"}
ADDRESS_KIND_PATCH = {"path": "third-parties/fortran/llvm23-flang-wasm32-address-kind.patch",
                      "sha256": "f1245bb1f3ebac4dcc00ef7c2e9fb4826001fdc83625f6c94a29bd8ca286d1f1"}
CFI_LAYOUT_PATCH = {"path": "third-parties/fortran/llvm23-flang-target-cfi-layout.patch",
                    "sha256": "8b82a92db84ee9ca3333df2b033975e9abcc73b81f8d398c64e80b35fe66e5d8"}
MULTI_TARGET_DEVELOPMENT_FLANG = "4756550cedf51ed844b32436270d89ad73b590a3c13b504b3ac8db9935cc8702"


def llvm_recipe_digest(entry):
    """Bind the upstream archive and the ordered patches used to build Flang."""
    fields = {key: entry[key] for key in ("revision", "archive_sha256", "patches")}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def identity(binary):
    return dict(format="wros-flang-wasm-producer", llvm_revision=LLVM_REVISION,
                llvm_recipe_sha256=LLVM_RECIPE_SHA256, patch_sha256=ABI_PATCH["sha256"],
                globals_header_sha256=GLOBALS_HEADER_PATCH["sha256"], extent_sha256=ASSUMED_EXTENT_PATCH["sha256"],
                address_kind_sha256=ADDRESS_KIND_PATCH["sha256"], cfi_layout_sha256=CFI_LAYOUT_PATCH["sha256"],
                compiler_sha256=digest(binary), targets=["WebAssembly"])


def require_compiler(binary):
    expected = identity(binary)
    if expected["compiler_sha256"] == MULTI_TARGET_DEVELOPMENT_FLANG:
        raise ValueError("the multi-target development Flang cannot be used by this SDK")
    record = binary.with_name(binary.name + ".json")
    if not record.is_file() or record.stat().st_size > 1024 or json.loads(record.read_bytes()) != expected:
        raise ValueError("unrecognized Flang; build the WebAssembly-only compiler with build_flang.py")
