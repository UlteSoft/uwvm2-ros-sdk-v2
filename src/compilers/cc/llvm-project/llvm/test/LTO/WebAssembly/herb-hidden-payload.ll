; REQUIRES: webassembly-registered-target
; RUN: split-file %s %t
; RUN: llvm-as %t/def.ll -o %t/def.bc
; RUN: llvm-as %t/use.ll -o %t/use.bc
; RUN: not llvm-lto2 run %t/def.bc %t/use.bc -o %t/link -r=%t/def.bc,make,px -r=%t/use.bc,make, -r=%t/use.bc,start,px 2>&1 | FileCheck %s
; CHECK: herbception ODR violation: symbol 'make'
; CHECK-DAG: herbthrows_sret[0, 0](i64)
; CHECK-DAG: herbthrows_sret[0, 0](i32)

;--- def.ll
target datalayout = "e-m:e-p:32:32-p10:8:8-p20:8:8-i64:64-i128:128-n32:64-S128-ni:1:10:20"
target triple = "wasm32-unknown-unknown"
define i1 @make(ptr herbthrows_sret(i64) %dst) herbthrows {
  store i64 42, ptr %dst
  ret i1 false
}

;--- use.ll
target datalayout = "e-m:e-p:32:32-p10:8:8-p20:8:8-i64:64-i128:128-n32:64-S128-ni:1:10:20"
target triple = "wasm32-unknown-unknown"
declare i1 @make(ptr herbthrows_sret(i32)) herbthrows
define i1 @start(ptr %dst) {
  %failed = call i1 @make(ptr herbthrows_sret(i32) %dst)
  ret i1 %failed
}
