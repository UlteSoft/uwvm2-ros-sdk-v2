; RUN: llc < %s -asm-verbose=false | FileCheck %s

target triple = "wasm64-unknown-unknown"

; --- FF / packed 0x01010020: memtag.status ---
; CHECK-LABEL: test_status:
; CHECK: memtag.status 0
define i64 @test_status() {
  %1 = call i64 @llvm.wasm.memtag.status.i64(i32 0)
  ret i64 %1
}

; --- FF / packed 0x01010021: memtag.extract ---
; CHECK-LABEL: test_extract:
; CHECK: local.get 0
; CHECK: memtag.extract 0
define i64 @test_extract(ptr %p) {
  %1 = call i64 @llvm.wasm.memtag.extract.i64(i32 0, ptr %p)
  ret i64 %1
}

; --- FF / packed 0x01010022: memtag.insert ---
; CHECK-LABEL: test_insert:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.insert 0
define ptr @test_insert(ptr %p, i64 %v) {
  %1 = call ptr @llvm.wasm.memtag.insert.i64(i32 0, ptr %p, i64 %v)
  ret ptr %1
}

; --- FF / packed 0x01010023: memtag.tagbits ---
; CHECK-LABEL: test_tagbits:
; CHECK: memtag.tagbits 0
define i64 @test_tagbits() {
  %1 = call i64 @llvm.wasm.memtag.tagbits.i64(i32 0)
  ret i64 %1
}

; --- FF / packed 0x01010024: memtag.startbit ---
; CHECK-LABEL: test_startbit:
; CHECK: memtag.startbit 0
define i64 @test_startbit() {
  %1 = call i64 @llvm.wasm.memtag.startbit.i64(i32 0)
  ret i64 %1
}

; --- FF / packed 0x01010025: memtag.copy ---
; CHECK-LABEL: test_copy:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.copy 0
define ptr @test_copy(ptr %d, ptr %s) {
  %1 = call ptr @llvm.wasm.memtag.copy(i32 0, ptr %d, ptr %s)
  ret ptr %1
}

; --- FF / packed 0x01010026: memtag.sub ---
; CHECK-LABEL: test_sub:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.sub 0
define i64 @test_sub(ptr %a, ptr %b) {
  %1 = call i64 @llvm.wasm.memtag.sub.i64(i32 0, ptr %a, ptr %b)
  ret i64 %1
}

; --- FF / packed 0x01010027: memtag.load ---
; CHECK-LABEL: test_load:
; CHECK: local.get 0
; CHECK: memtag.load 0
define ptr @test_load(ptr %p) {
  %1 = call ptr @llvm.wasm.memtag.load(i32 0, ptr %p)
  ret ptr %1
}

; --- FF / packed 0x01010028: memtag.untag ---
; CHECK-LABEL: test_untag:
; CHECK: local.get 0
; CHECK: memtag.untag 0
define ptr @test_untag(ptr %p) {
  %1 = call ptr @llvm.wasm.memtag.untag(i32 0, ptr %p)
  ret ptr %1
}

; --- FF / packed 0x01010029: memtag.untagstore ---
; CHECK-LABEL: test_untagstore:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.untagstore 0
define ptr @test_untagstore(ptr %p, i64 %v) {
  %1 = call ptr @llvm.wasm.memtag.untagstore.i64(i32 0, ptr %p, i64 %v)
  ret ptr %1
}

; --- FF / packed 0x0101002a: memtag.untagstorez ---
; CHECK-LABEL: test_untagstorez:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.untagstorez 0
define ptr @test_untagstorez(ptr %p, i64 %v) {
  %1 = call ptr @llvm.wasm.memtag.untagstorez.i64(i32 0, ptr %p, i64 %v)
  ret ptr %1
}

; --- FF / packed 0x0101002b: memtag.store ---
; CHECK-LABEL: test_store:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.store 0
define void @test_store(ptr %p, i64 %v) {
  call void @llvm.wasm.memtag.store.i64(i32 0, ptr %p, i64 %v)
  ret void
}

; --- FF / packed 0x0101002c: memtag.storez ---
; CHECK-LABEL: test_storez:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.storez 0
define void @test_storez(ptr %p, i64 %v) {
  call void @llvm.wasm.memtag.storez.i64(i32 0, ptr %p, i64 %v)
  ret void
}

; --- FF / packed 0x0101002d: memtag.random ---
; CHECK-LABEL: test_random:
; CHECK: local.get 0
; CHECK: memtag.random 0
define ptr @test_random(ptr %p) {
  %1 = call ptr @llvm.wasm.memtag.random(i32 0, ptr %p)
  ret ptr %1
}

; --- FF / packed 0x0101002e: memtag.randomstore ---
; CHECK-LABEL: test_randomstore:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.randomstore 0
define ptr @test_randomstore(ptr %p, i64 %v) {
  %1 = call ptr @llvm.wasm.memtag.randomstore.i64(i32 0, ptr %p, i64 %v)
  ret ptr %1
}

; --- FF / packed 0x0101002f: memtag.randomstorez ---
; CHECK-LABEL: test_randomstorez:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: memtag.randomstorez 0
define ptr @test_randomstorez(ptr %p, i64 %v) {
  %1 = call ptr @llvm.wasm.memtag.randomstorez.i64(i32 0, ptr %p, i64 %v)
  ret ptr %1
}

; --- FF / packed 0x01010033: memtag.add ---
; CHECK-LABEL: test_add:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: local.get 2
; CHECK: memtag.add 0
define ptr @test_add(ptr %p, i64 %o, i64 %t) {
  %1 = call ptr @llvm.wasm.memtag.add.i64(i32 0, ptr %p, i64 %o, i64 %t)
  ret ptr %1
}

; --- FF / packed 0x01010036: memtag.hint ---
; CHECK-LABEL: test_hint:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: local.get 2
; CHECK: memtag.hint 0
define ptr @test_hint(ptr %p, ptr %h, i64 %i) {
  %1 = call ptr @llvm.wasm.memtag.hint.i64(i32 0, ptr %p, ptr %h, i64 %i)
  ret ptr %1
}

; --- FF / packed 0x01010037: memtag.hintstore ---
; CHECK-LABEL: test_hintstore:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: local.get 2
; CHECK: local.get 3
; CHECK: memtag.hintstore 0
define ptr @test_hintstore(ptr %p, i64 %v, ptr %h, i64 %i) {
  %1 = call ptr @llvm.wasm.memtag.hintstore.i64(i32 0, ptr %p, i64 %v, ptr %h, i64 %i)
  ret ptr %1
}

; --- FF / packed 0x01010038: memtag.hintstorez ---
; CHECK-LABEL: test_hintstorez:
; CHECK: local.get 0
; CHECK: local.get 1
; CHECK: local.get 2
; CHECK: local.get 3
; CHECK: memtag.hintstorez 0
define ptr @test_hintstorez(ptr %p, i64 %v, ptr %h, i64 %i) {
  %1 = call ptr @llvm.wasm.memtag.hintstorez.i64(i32 0, ptr %p, i64 %v, ptr %h, i64 %i)
  ret ptr %1
}

; --- Intrinsic Declarations ---
declare i64 @llvm.wasm.memtag.status.i64(i32)
declare i64 @llvm.wasm.memtag.extract.i64(i32, ptr)
declare ptr @llvm.wasm.memtag.insert.i64(i32, ptr, i64)
declare i64 @llvm.wasm.memtag.tagbits.i64(i32)
declare i64 @llvm.wasm.memtag.startbit.i64(i32)
declare ptr @llvm.wasm.memtag.copy(i32, ptr, ptr)
declare i64 @llvm.wasm.memtag.sub.i64(i32, ptr, ptr)
declare ptr @llvm.wasm.memtag.load(i32, ptr)
declare ptr @llvm.wasm.memtag.untag(i32, ptr)
declare ptr @llvm.wasm.memtag.untagstore.i64(i32, ptr, i64)
declare ptr @llvm.wasm.memtag.untagstorez.i64(i32, ptr, i64)
declare void @llvm.wasm.memtag.store.i64(i32, ptr, i64)
declare void @llvm.wasm.memtag.storez.i64(i32, ptr, i64)
declare ptr @llvm.wasm.memtag.random(i32, ptr)
declare ptr @llvm.wasm.memtag.randomstore.i64(i32, ptr, i64)
declare ptr @llvm.wasm.memtag.randomstorez.i64(i32, ptr, i64)
declare ptr @llvm.wasm.memtag.add.i64(i32, ptr, i64, i64)
declare ptr @llvm.wasm.memtag.hint.i64(i32, ptr, ptr, i64)
declare ptr @llvm.wasm.memtag.hintstore.i64(i32, ptr, i64, ptr, i64)
declare ptr @llvm.wasm.memtag.hintstorez.i64(i32, ptr, i64, ptr, i64)
