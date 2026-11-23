"""Generate callable Python raw bindings from the VM registration and wire contracts."""
import json
from pathlib import Path
import sys
from textwrap import wrap

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from language_contract import authority, domains, memory_contract, parameters, result_text

DEST = HERE.parents[1] / "include/u2rosv2/universal/py/uwrosv2"


def binding(row):
    name = row["name"]
    params = row["parameters"]
    formal = ", ".join(p["name"] for p in params)
    args = parameters(row)
    docs = [row["contract"].strip(), authority(row), memory_contract(row)]
    for p in params:
        docs.append(f"{p['name']} ({p['type']}, unsigned bit pattern). {args[p['name']]}")
    docs.append("Returns an i32 as a Python int. " + result_text(row))
    body = "\n\n".join("\n".join(wrap(p, 92, break_long_words=False, break_on_hyphens=False)) for p in docs)
    signature = f"def wr_{name.replace('.', '_')}({formal}):"
    call = ", " + formal if formal else ""
    return (signature + '\n    """' + body.replace("\n", "\n    ").replace("    \n", "\n") +
            '"""\n' + f"    return raw({name!r}{call})\n")


def main():
    contract = json.loads((HERE / "contract.json").read_bytes())
    for domain, rows in domains(contract).items():
        module = domain.replace("-", "_")
        if not module.isidentifier():
            raise ValueError("unexpected Python domain " + module)
        header = f'"""Raw {domain} imports from {contract["module"]}."""\nfrom _uwros_runtime import raw\n'
        (DEST / (module + ".py")).write_text(header + "\n\n" + "\n\n".join(binding(row) for row in rows))
    statuses = "\n".join(f"{name.upper()} = {value}" for name, value in contract["statuses"].items())
    (DEST / "status.py").write_text('"""Carrier status numbers returned by uwvm_ros_v2."""\n' + statuses + "\n")


if __name__ == "__main__":
    main()
