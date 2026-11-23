; RUN: llc < %s -verify-each -stop-after=WebAssembly-globals-tagging | FileCheck %s
; RUN: llc < %s -verify-each -filetype=obj -o /dev/null

target triple = "wasm32-unknown-unknown"
@arr = global [16 x i8] zeroinitializer, sanitize_memtag, align 16

; Rewritten expressions belong to their incoming blocks, not the PHI block.
; CHECK-LABEL: define ptr @phi_edges(
; CHECK: entry:
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @arr)
; CHECK: left:
; CHECK: getelementptr
; CHECK: br label %join
; CHECK: right:
; CHECK: getelementptr
; CHECK: br label %join
; CHECK: join:
; CHECK-NEXT: %a = phi ptr
; CHECK-NEXT: %b = phi i32
define ptr @phi_edges(i1 %cond) {
entry:
  br i1 %cond, label %left, label %right
left:
  br label %join
right:
  br label %join
join:
  %a = phi ptr [ getelementptr ([16 x i8], ptr @arr, i32 0, i32 1), %left ],
               [ getelementptr ([16 x i8], ptr @arr, i32 0, i32 2), %right ]
  %b = phi i32 [ 1, %left ], [ 2, %right ]
  %result = getelementptr i8, ptr %a, i32 %b
  ret ptr %result
}

; A loop backedge/critical edge must retain PHI grouping and dominance.
; CHECK-LABEL: define ptr @loop(
; CHECK: loop:
; CHECK-NEXT: %p = phi ptr
define ptr @loop(i1 %again) {
entry:
  br label %loop
loop:
  %p = phi ptr [ getelementptr ([16 x i8], ptr @arr, i32 0, i32 3), %entry ],
               [ getelementptr ([16 x i8], ptr @arr, i32 0, i32 4), %loop ]
  br i1 %again, label %loop, label %exit
exit:
  ret ptr %p
}

; Recursively expanded operands must precede their users.
; CHECK-LABEL: define i32 @nested(
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @arr)
; CHECK: getelementptr
; CHECK: ptrtoint
define i32 @nested() {
  ret i32 ptrtoint (ptr getelementptr ([16 x i8], ptr @arr, i32 0, i32 5) to i32)
}
