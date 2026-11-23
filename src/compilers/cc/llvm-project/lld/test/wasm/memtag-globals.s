# RUN: llvm-mc -filetype=obj -triple=wasm32-unknown-unknown %s -o %t.o
# RUN: wasm-ld --no-entry --no-gc-sections -o %t.wasm %t.o
# RUN: llvm-objdump -s %t.wasm | FileCheck %s
# RUN: wasm-ld --no-entry --no-gc-sections --relocatable -o %t.rel.o %t.o
# RUN: llvm-objdump -s %t.rel.o | FileCheck %s --check-prefix=RELOC
# RUN: llvm-mc -filetype=obj -triple=wasm64-unknown-unknown %s -o %t64.o
# RUN: wasm-ld -mwasm64 --no-entry --no-gc-sections -o %t64.wasm %t64.o
# RUN: llvm-objdump -s %t64.wasm | FileCheck %s
# RUN: wasm-ld -mwasm64 --no-entry --no-gc-sections --relocatable -o %t64.rel.o %t64.o
# RUN: llvm-objdump -s %t64.rel.o | FileCheck %s --check-prefix=RELOC

# The linker synthesizes a "uwvm.memtag.linear.globals" custom section describing the
# address and size of every live data symbol carrying the memtag flag.
# The payload is: ULEB version (2), ULEB count, then (ULEB memory index,
# ULEB address, ULEB size) triples sorted by address. The memory index is zero. Untagged symbols are not listed.
# The encoding is identical for wasm64 since addresses are ULEB-encoded.

        .memtag tagged16b
        .globl  tagged16b
        .section .data.tagged16b,"",@
        .p2align 4
tagged16b:
        .int32  42
        .size tagged16b, 16

        .memtag local16b
        .section .data.local16b,"",@
        .p2align 4
local16b:
        .int32  1
        .int32  2
        .int32  3
        .int32  4
        .size local16b, 16

        .memtag tagged32b
        .globl  tagged32b
        .section .data.tagged32b,"",@
        .p2align 4
tagged32b:
        .int64  1
        .int64  2
        .int64  3
        .int64  4
        .size tagged32b, 32

        .globl  plain
        .section .data.plain,"",@
        .p2align 2
plain:
        .int32  7
        .size plain, 4

# CHECK:      Contents of section uwvm.memtag.linear.globals:
# CHECK-NEXT: {{^ [0-9a-f]+ }}02030080 80041000 90800410 00a08004
# CHECK-NEXT: {{^ [0-9a-f]+ }}20

# Relocatable output has no final addresses, and PIC output has none either,
# so the descriptor section is omitted.
# RELOC-NOT: Contents of section uwvm.memtag.linear.globals:
