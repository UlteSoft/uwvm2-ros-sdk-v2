"""Render standalone WAT import modules with the registered i32/i64 signatures."""
from pathlib import Path
from language_contract import comment, domains

PUBLIC = Path("include/u2rosv2/universal/wat/uwrosv2")


def render(contract):
    files = {}
    for name, rows in {**domains(contract), "scene": contract["operations"]}.items():
        lines = [";; Generated from src/abi/contract.json. Copy the required imports into the calling",
                 ";; guest and declare each one with wrwat --ros-operation. Guest addresses refer to",
                 ";; the immediate caller's linear memory.", "(module"]
        exports = []
        for row in rows:
            symbol = "$wr_" + row["name"].replace(".", "_")
            sig = row["wasm_signature"]
            inputs = "".join(f' (param ${p["name"]} {p["type"]})' for p in row["parameters"])
            outputs = "" if not sig["results"] else " (result " + " ".join(sig["results"]) + ")"
            lines.extend(["", comment(row, style="wat")])
            lines.append(f'  (import "{contract["module"]}" "{row["name"]}" (func {symbol}{inputs}{outputs}))')
            exports.append(f'  (export "{row["name"]}" (func {symbol}))')
        files[PUBLIC / (name + ".wat")] = "\n".join([*lines, "", *exports, ")", ""])
    return files
