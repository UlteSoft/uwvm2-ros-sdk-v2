"""@file abi_reference.py
@brief Emit an English Doxygen entry for every operation in the pinned ROSv2 C ABI.
@details The documentation is adjacent to the source interface in Doxygen. Keeping the
text separate preserves the digest of the signed compiler input header.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARRIER = (
    "Capability or object handle required by this operation.",
    "Index of the caller's linear memory.",
    "Address of the request bytes in that memory.",
    "Number of request bytes.",
    "Address of the caller's response buffer.",
    "Response buffer capacity in bytes.",
    "Address at which the host reports the response length, as a 64-bit word.",
)
SPECIAL = {
    "abi": (),
    "capability.open": ("Index of the caller's linear memory.", "Address of the alias text.",
                        "Length of the alias in bytes.", "Address of the resulting 64-bit capability handle."),
    "capability.close": ("Live capability handle owned by this caller.",),
}


def fields(rows):
    """@brief Format typed record fields in declaration order."""
    return ", ".join(row["name"] + " (" + row["type"] + ")" for row in rows) or "none"


def render(abi):
    """@brief Bind each C declaration to its exact wire schema, authority and result."""
    text = ["/** @file ros-abi.dox", " * @brief Raw ROSv2 imports and guest memory contracts.", " */", ""]
    for op in abi["operations"]:
        name = op["name"]
        params = op["wasm_signature"]["parameters"]
        fields_in = SPECIAL.get(name, CARRIER)
        if len(fields_in) != len(params):
            raise ValueError("undocumented signature: " + name)
        args = ", ".join(f"uint{kind[1:]}_t arg{i}" for i, kind in enumerate(params)) or "void"
        label = "wr_" + name.replace(".", "_").replace("-", "_")
        text.extend([f"/** @fn uint32_t {label}({args})", " * @brief " + op["contract"],
                     f" * @details Guest import <tt>{abi['module']}.{name}</tt>.",
                     " * Wire format: " + op["wire"] + ".",
                     " * Request fields: " + fields(op["request"]) + ".",
                     " * Result fields: " + fields(op["result"]) + ".",
                     " * Host action: " + op["action"] + "."])
        if op["purposes"]:
            text.append(" * Applicable resource purposes: " + ", ".join(op["purposes"]) + ".")
        for i, description in enumerate(fields_in):
            text.append(f" * @param arg{i} {description}")
        ret = ("The ROSv2 ABI major, or a host error." if name == "abi"
               else "The ROSv2 status code. Interpret response fields according to the operation contract.")
        text.extend([" * @return " + ret, " */", ""])
    return "\n".join(text)


if __name__ == "__main__":
    source = json.loads((ROOT / "share/abi/ros.json").read_bytes())
    (ROOT / "document/source/ros-abi.dox").write_text(render(source), encoding="utf-8")
