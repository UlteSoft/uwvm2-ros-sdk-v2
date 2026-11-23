; RUN: llc -mtriple=wasm32 -mattr=+multivalue < %s | FileCheck %s
; RUN: llc -mtriple=wasm32 -mattr=+multivalue -global-isel -global-isel-abort=0 < %s | FileCheck %s
; RUN: llc -mtriple=wasm64 -mattr=+multivalue < %s | FileCheck %s

; A plain caller and an indirect call use the callee's Herb ABI. The global
; materializes an independently callable target with the same function type.
@slot = global ptr @target
declare { i64, i1 } @target(i64) herbthrows
; CHECK: .functype target (i64) -> (i64, i32)
define i64 @plain_caller(i64 %x) {
; CHECK-LABEL: plain_caller:
; CHECK: call_indirect
  %callee = load volatile ptr, ptr @slot
  %result = call { i64, i1 } %callee(i64 %x) herbthrows
  %value = extractvalue { i64, i1 } %result, 0
  %failed = extractvalue { i64, i1 } %result, 1
  %ret = select i1 %failed, i64 -1, i64 %value
  ret i64 %ret
}
