"""Compare actual Wasm import and type sections to the registered VM contract."""
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import subprocess

WORK = Path("/work")
OUT = WORK / "out"
CONTRACT = json.loads((WORK / "src/abi/contract.json").read_text())
LANGUAGES = ("c", "cpp", "rust")
TYPES = {0x7F: "i32", 0x7E: "i64", 0x7D: "f32", 0x7C: "f64",
         0x7B: "v128", 0x70: "funcref", 0x6F: "externref"}


@dataclass
class Reader:
    stream: io.BytesIO

    def take(self, size):
        value = self.stream.read(size)
        if len(value) != size:
            raise ValueError(f"truncated Wasm at {self.stream.tell()}")
        return value

    def byte(self):
        return self.take(1)[0]

    def leb(self):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if byte & 128 == 0:
                return value
        raise ValueError("invalid u32")

    def vec(self, decode):
        return [decode() for _ in range(self.leb())]

    def name(self):
        return self.take(self.leb()).decode("utf-8")


def wasm_table(wasm):
    binary = Reader(io.BytesIO(wasm))
    assert binary.take(8) == b"\x00asm\x01\x00\x00\x00"
    types, imports, exports = [], {}, {}
    while binary.stream.tell() < len(wasm):
        section_id = binary.byte()
        body = Reader(io.BytesIO(binary.take(binary.leb())))
        if section_id == 1:
            def function_type():
                assert body.byte() == 0x60
                parameters = body.vec(lambda: TYPES[body.byte()])
                results = body.vec(lambda: TYPES[body.byte()])
                return {"parameters": parameters, "results": results}
            types = body.vec(function_type)
        elif section_id == 2:
            for _ in range(body.leb()):
                module, name = body.name(), body.name()
                assert body.byte() == 0, (module, name, "expected function import")
                assert (module, name) not in imports, (module, name, "duplicate import")
                imports[module, name] = types[body.leb()]
        elif section_id == 7:
            for _ in range(body.leb()):
                name, kind, index = body.name(), body.byte(), body.leb()
                if kind == 0:
                    exports[name] = index
        else:
            continue
        assert body.stream.read(1) == b"", "trailing data in parsed section"
    return imports, exports


def main():
    expected = {(CONTRACT["module"], op["name"]): op["wasm_signature"]
                for op in CONTRACT["operations"]}
    assert len(expected) == len(CONTRACT["operations"]) == 163
    guard_names = {"abi", "capability.open", "capability.close", "guard.create",
                   "guard.take", "guard.trigger", "resource.close"}
    report = {}
    for lang in LANGUAGES:
        report[lang] = {}
        for name, filter_names, export in (("all", None, "_start"),
                                           ("abi", {"abi"}, "test_abi"),
                                           ("guard", guard_names, "_start")):
            path = OUT / lang / (name + ".wasm")
            data = path.read_bytes()
            imports, exports = wasm_table(data)
            subset = {k: v for k, v in expected.items() if filter_names is None or k[1] in filter_names}
            assert imports.keys() == subset.keys(), (path, "unexpected", sorted(imports.keys() - subset.keys()),
                                                     "missing", sorted(subset.keys() - imports.keys()))
            for k in imports:
                assert imports[k] == subset[k], (path, k, imports[k], subset[k])
            assert export in exports and exports[export] >= len(imports)
            report[lang][name] = {
                "import_count": len(imports),
                "sha256": hashlib.sha256(data).hexdigest(),
                "entry_local_index": exports[export] - len(imports),
                "imports": [{"module": k[0], "name": k[1], **v} for k, v in sorted(imports.items())],
            }
            with path.with_suffix(".objdump.txt").open("w") as log:
                subprocess.run(["wasm-objdump", "-x", path], stdout=log, stderr=subprocess.STDOUT, check=True)
            print(f"PASS {lang}/{name} {len(imports)} exact imports, {export} local index {exports[export] - len(imports)}",
                  flush=True)
    (OUT / "import-tables.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
