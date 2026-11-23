"""Read the actual ROSv2 local-import tuple and join its entries to VM wire metadata."""

import csv
import hashlib
import json
import re
from pathlib import Path


HOST = Path("src/uwvm2/uwvm/imported/scene/host.h")
ROS = Path("src/uwvm2/imported/ros")
CATALOGUE = Path("tools/ros_scene/interface-catalogue.json")
DESIGN = Path("tools/ros_scene/operation-contracts.json")
SCALAR = {"32": "i32", "64": "i64"}


def require(value, message):
    if not value:
        raise ValueError(message)
    return value


def unique(rows, key):
    result = {}
    for row in rows:
        name = row[key]
        require(name not in result, f"duplicate {key} {name}")
        result[name] = row
    return result


def signature(host, handler):
    prototype = require(re.search(
        rf"inline\s+std::uint(32|64)_t\s+{handler}\s*\(([^()]*)\)\s*noexcept", host
    ), f"unsupported host prototype for {handler}")
    parameters = []
    for arg in filter(None, prototype[2].split(",")):
        item = require(re.fullmatch(r"\s*std::uint(32|64)_t\s+(\w+)\s*", arg),
                       f"unsupported parameter in {handler}: {arg!r}")
        parameters.append({"name": item[2], "type": SCALAR[item[1]]})
    return parameters, {"parameters": [p["type"] for p in parameters], "results": [SCALAR[prototype[1]]]}


def registered(root, host, sources):
    # The actual wrapper pointers in local_function_tuple select both the native
    # prototype and the external name. Design-only macros elsewhere are ignored.
    module = require(re.search(r'module_name\s*\{u8"([^"]+)"\}', host), "missing module name")[1]
    block = require(re.search(r"using local_function_tuple\s*=.*?tuple<(.*?)>;", host, re.S),
                    "missing host registration tuple")[1]
    joined = re.sub(r"\\\s*\n", " ", block)
    adapters = {}
    tables = {}
    direct = []
    for line in map(str.strip, joined.splitlines()):
        if not line or line.startswith("#undef "):
            continue
        adapter = re.fullmatch(r"#define\s+(\w+)\(([^)]*)\)\s+wrapper::native<&(\w+)"
                               r"(?:<[^;]*>)?,\s*wrapper::symbol##_name>,", line)
        if adapter:
            args = [s.strip() for s in adapter[2].split(",")]
            adapters[adapter[1]] = (adapter[3], args.index("external"))
            continue
        table = re.fullmatch(r"(UWVM_ROS_\w+_FUNCTIONS)\((\w+)\)", line)
        if table:
            require(table[1] not in tables and table[2] in adapters, f"unknown tuple row {line}")
            tables[table[1]] = adapters[table[2]]
            continue
        rows = re.findall(r"wrapper::native<&(\w+),\s*wrapper::(\w+_name)>", line)
        require(rows and not re.sub(r"wrapper::native<&\w+,\s*wrapper::\w+_name>|[\s,]", "", line),
                f"unrecognised registration syntax: {line}")
        direct.extend(rows)

    definitions = {}
    for directory in ("runtime", "scene"):
        for path in sorted((root / ROS / directory).glob("*.h")):
            content = re.sub(r"\\[^\S\n]*\n", " ", path.read_text())
            for match in re.finditer(r"^#define\s+(UWVM_ROS_\w+_FUNCTIONS)\(X\)\s+([^\n]*)", content, re.M):
                name = match[1]
                if name in tables:
                    require(name not in definitions, f"duplicate table {name}")
                    definitions[name] = (path.relative_to(root), match[2].strip())
    require(definitions.keys() == tables.keys(), "registration table missing from VM source")
    entries = []
    for table, (handler, external_index) in tables.items():
        path, list_body = definitions[table]
        sources.add(path)
        require(not re.sub(r"\bX\([^()]*\)|\s+", "", list_body), f"unsupported table body in {table}")
        for row in re.findall(r"\bX\(([^()]*)\)", list_body):
            fields = next(csv.reader([row], skipinitialspace=True))
            name = fields[external_index].strip()
            require(re.fullmatch(r"[a-z][a-z0-9_.]*", name), f"unknown import name {name}")
            entries.append((name, handler, str(path), table))
    for handler, symbol in direct:
        name = require(re.search(rf'\b{symbol}\[\]\s*=\s*u8"([^"]+)"', host),
                       f"missing literal for {symbol}")[1]
        entries.append((name, handler, str(HOST), None))
    return module, entries


def extract(vm_root):
    root = vm_root.resolve()
    host = (root / HOST).read_text()
    catalogue = json.loads((root / CATALOGUE).read_text())
    design = json.loads((root / DESIGN).read_text())
    sources = {HOST, CATALOGUE, DESIGN, ROS / "runtime/resources.h", ROS / "scene/wire.h"}
    module, entries = registered(root, host, sources)
    require(module == catalogue["abi_module"] == design["abi_module"], "module mismatch")
    rows = unique((r for r in catalogue["operations"] if r["implementation"] == "registered_local"), "name")
    semantics = unique(design["operations"], "operation")
    names = [e[0] for e in entries]
    require(len(names) == len(set(names)), "duplicate import in registration")
    require(set(names) == set(rows), f"catalogue and VM registrations differ: {set(names) ^ set(rows)}")
    # Match the primitive-width conversion actually used by the wrapper template.
    require(re.search(r"sizeof\(T\)\s*<=\s*4\s*\?\s*value::i32\s*:\s*value::i64", host),
            "VM primitive width mapping changed")
    operations = []
    for name, handler, path, table in sorted(entries):
        entry = rows[name]
        parameters, wasm = signature(host, handler)
        require(entry["wasm_signature"] == wasm, f"catalogue signature differs from handler {handler} for {name}")
        domain = name.partition(".")[0]
        if name.startswith("module.call."):
            domain = "module_call"
        domain = {"abi": "capability", "type": "types", "module": "modules"}.get(domain, domain)
        operation = {k: entry[k] for k in ("name", "family", "action", "purposes", "secondary_actions",
                       "wire", "request", "result", "contract", "request_words", "result_bytes",
                       "implementation_scope") if k in entry}
        operation.update(domain=domain, parameters=parameters, wasm_signature=wasm,
                         registration={"table": table, "source": path, "handler": handler},
                         behavior=semantics[name]["behavior"])
        operations.append(operation)
    resource_text = (root / ROS / "runtime/resources.h").read_text()
    enum = require(re.search(r"enum class error\s*:\s*std::uint32_t\s*\{([^{}]*)\}", resource_text),
                   "missing scene result codes")[1]
    statuses = {}
    for item in enum.split(","):
        status = require(re.fullmatch(r"\s*(\w+)\s*=\s*(\d+)\s*", item), f"unrecognised scene error: {item}")
        statuses[status[1]] = int(status[2])
    return {
        "format": 1, "module": module, "statuses": statuses, "encoding": catalogue["encoding"],
        "source_sha256": {str(p): hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sorted(sources)},
        "schemas": catalogue["schemas"], "operations": operations,
    }
