"""@file extend.py
@brief Add the VM's packed linear WasmMTE instruction family to the pinned toolchain."""
from pathlib import Path
import sys


OPS = (
    "status", "extract", "insert", "tagbits", "startbit", "copy", "sub", "load",
    "untag", "untagstore", "untagstorez", "store", "storez", "random", "randomstore", "randomstorez",
)
MANAGED = ("claim", "claimz", "reserve", "activate", "release")
INSTRUCTIONS = (*enumerate(OPS, 0x20), *enumerate(("hint", "hintstore", "hintstorez"), 0x36),
                *enumerate(MANAGED, 0x40))


def extend(root):
    """@brief Extend text resolution, byte emission and final-binary validation together."""
    wast = root / "wast-263.0.0/src/core"
    encoder = root / "wasm-encoder-0.263.0/src/core/instructions.rs"
    parser = root / "wasmparser-memtag/src"

    def insert(path, marker, lines):
        text = path.read_text()
        if text.count(marker) != 1:
            raise ValueError(f"unexpected upstream patch site: {path}")
        path.write_text(text.replace(marker, marker + lines))

    insert(wast / "expr.rs", '        memory_fill(MemoryArg<\'a>) : "memory.fill",\n', "".join(
        f'        #[custom_encode]\n        memtag_{name}(MemoryArg<\'a>) : "memtag.{name}",\n'
        for _, name in INSTRUCTIONS
    ))
    insert(wast / "resolve/names.rs", "        match instr {\n", "".join(
        f'            I::memtag_{name}(i) => {{ self.resolver.resolve(&mut i.mem, Ns::Memory)?; }}\n'
        for _, name in INSTRUCTIONS
    ))
    insert(encoder, "    // Control instructions.\n", """
    /// Encode a reviewed linear WasmMTE instruction and its memory index.
    pub fn wros_memtag(&mut self, operation: u16, memory: u32) {
        self.sink.push(0xff);
        (0x0101_0000_u32 | u32::from(operation)).encode(self.sink);
        memory.encode(self.sink);
    }
""")
    insert(wast / "binary.rs", "pub(crate) mod custom_encoders {\n    use super::*;\n", "".join(
        f'\n    pub(crate) fn memtag_{name}(sink: &mut InstructionSink<\'_>, memory: &MemoryArg<\'_>) {{\n'
        f'        sink.wros_memtag(0x{code:02x}, memory.into());\n    }}\n'
        for code, name in INSTRUCTIONS
    ))
    insert(parser / "lib.rs", "                MemtagHintstorez { mem: u32 } => visit_memtag_hintstorez (arity 4 -> 1)\n",
           "".join(f'                Memtag{name.title()} {{ mem: u32 }} => visit_memtag_{name} (arity 2 -> 1)\n'
                   for name in MANAGED))
    insert(parser / "binary_reader.rs", "            0x0101_0038 => memory_instruction!(visit_memtag_hintstorez),\n",
           "".join(f'            0x0101_00{code:02x} => memory_instruction!(visit_memtag_{name}),\n'
                   for code, name in enumerate(MANAGED, 0x40)))
    insert(parser / "validator/operators.rs", "    fn visit_memtag_status(&mut self, mem: u32) -> Self::Output {\n"
           "        let ty = self.check_memory_index(mem)?;\n        self.push_operand(ty)?;\n        Ok(())\n    }\n",
           "".join(f'    fn visit_memtag_{name}(&mut self, mem: u32) -> Self::Output {{\n'
                   f'        self.visit_memtag_untagstore(mem)\n    }}\n' for name in MANAGED))


if __name__ == "__main__":
    extend(Path(sys.argv[1]))
