# RUN: llvm-mc -filetype=obj -triple=wasm32-unknown-unknown %s -o %t.o
# RUN: not wasm-ld --shared-memory --max-memory=131072 --no-entry --no-gc-sections %t.o -o %t.bad 2>&1 | FileCheck %s --check-prefix=DENY
# RUN: not wasm-ld --require-managed-tls --allow-legacy-tagged-tls --no-entry %t.o -o %t.bad 2>&1 | FileCheck %s --check-prefix=CONFLICT
# RUN: wasm-ld -r %t.o -o %t.partial
# RUN: not wasm-ld --shared-memory --max-memory=131072 --no-entry --no-gc-sections %t.partial -o %t.bad 2>&1 | FileCheck %s --check-prefix=DENY
# RUN: wasm-ld --shared-memory --max-memory=131072 --no-entry --gc-sections %t.o -o %t.dead.wasm
# RUN: wasm-ld --allow-legacy-tagged-tls --shared-memory --max-memory=131072 --no-entry --no-gc-sections %t.o -o %t.wasm
# RUN: llvm-objdump -d --no-show-raw-insn --no-leading-addr %t.wasm | FileCheck %s

# DENY: --require-managed-tls: live tagged thread-local object {{first|second}} requires a dedicated TLS allocation and retirement contract
# CONFLICT: --require-managed-tls is incompatible with --allow-legacy-tagged-tls

# An explicitly requested legacy image retains the historical tag writes and
# preserves the initializer bytes. The strict default rejects this live layout.
.globaltype __tls_base, i32
.memtag first
.section .tdata.first,"T",@
.globl first
.p2align 4
first:
.int32 37
.skip 12
.size first, 16

.memtag second
.section .tbss.second,"T",@
.globl second
.p2align 4
second:
.skip 32
.size second, 32

.section .custom_section.target_features,"",@
.int8 2
.int8 43
.int8 7
.ascii "atomics"
.int8 43
.int8 11
.ascii "bulk-memory"

# CHECK-LABEL: <__wasm_init_tls>:
# CHECK: memory.init
# CHECK: local.get 0
# CHECK-NEXT: i32.const 0
# CHECK-NEXT: i32.add
# CHECK-NEXT: i32.const 16
# CHECK-NEXT: memtag.randomstore 0
# CHECK-NEXT: drop
# CHECK-NEXT: local.get 0
# CHECK-NEXT: i32.const 16
# CHECK-NEXT: i32.add
# CHECK-NEXT: i32.const 32
# CHECK-NEXT: memtag.randomstore 0
# CHECK-NEXT: drop
# CHECK-NOT: memtag.randomstorez
# CHECK: end
