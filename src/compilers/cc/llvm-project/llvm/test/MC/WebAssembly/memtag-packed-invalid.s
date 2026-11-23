# RUN: split-file %s %t
# RUN: not llvm-mc -triple=wasm32-unknown-unknown -show-encoding %t/add.s 2>&1 | FileCheck %s --check-prefix=ADD
# RUN: not llvm-mc -triple=wasm64-unknown-unknown -show-encoding %t/negative.s 2>&1 | FileCheck %s --check-prefix=INDEX
# RUN: not llvm-mc -triple=wasm32-unknown-unknown -show-encoding %t/symbol.s 2>&1 | FileCheck %s --check-prefix=SYMBOL
# RUN: llvm-mc -triple=wasm32-unknown-unknown -disassemble %t/wide-index.txt 2>&1 | FileCheck %s --check-prefix=DECODE
# RUN: llvm-mc -triple=wasm32-unknown-unknown -disassemble %t/overlong-index.txt 2>&1 | FileCheck %s --check-prefix=DECODE
# RUN: llvm-mc -triple=wasm64-unknown-unknown -disassemble %t/wide-index.txt 2>&1 | FileCheck %s --check-prefix=DECODE
# RUN: llvm-mc -triple=wasm64-unknown-unknown -disassemble %t/overlong-index.txt 2>&1 | FileCheck %s --check-prefix=DECODE
# llvm-mc diagnoses failed disassembly with a warning and a successful CLI exit.
# Require rejection, not a fabricated status instruction, on both targets.
# DECODE-NOT: memtag.status
# DECODE: warning: invalid instruction encoding
# DECODE-NOT: memtag.status
# ADD: memtag.add is reserved; no executable semantics
# INDEX: memtag memory index must fit u32
# SYMBOL: memtag memory index must be an integer
#--- add.s
test:
  .functype test () -> ()
  unreachable
  memtag.add 0
  drop
  end_function
#--- negative.s
test:
  .functype test () -> ()
  unreachable
  memtag.status -1
  drop
  end_function
#--- symbol.s
test:
  .functype test () -> ()
  unreachable
  memtag.status unresolved_memory
  drop
  end_function
#--- wide-index.txt
0xff 0xa0 0x80 0x84 0x08 0x80 0x80 0x80 0x80 0x10
#--- overlong-index.txt
0xff 0xa0 0x80 0x84 0x08 0x80 0x80 0x80 0x80 0x80 0x00
