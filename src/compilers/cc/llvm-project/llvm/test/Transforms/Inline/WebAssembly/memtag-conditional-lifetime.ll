; RUN: opt -mtriple=wasm32-unknown-unknown -passes=inline -S %s | FileCheck %s --check-prefixes=ALL,MTE
; RUN: opt -mtriple=wasm64-unknown-unknown -passes=inline -S %s | FileCheck %s --check-prefixes=ALL,MTE
; RUN: sed 's/ sanitize_memtag//' %s | opt -mtriple=wasm32-unknown-unknown -passes=inline -S | FileCheck %s --check-prefixes=ALL,PLAIN

declare void @escape(ptr)
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)

define internal void @worker(i1 %use) sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  br i1 %use, label %work, label %done
work:
  %field = getelementptr inbounds i8, ptr %slot, i32 3
  call void @escape(ptr %field)
  call void @escape(ptr %field)
  call void @escape(ptr %field)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}

; ALL-LABEL: define void @usually_bypassed(
; MTE: call void @worker(
; PLAIN: call void @escape(
define void @usually_bypassed(i1 %take, i1 %use) sanitize_memtag {
  br i1 %take, label %call, label %done, !prof !0
call:
  call void @worker(i1 %use)
  br label %done
done:
  ret void
}

; ALL-LABEL: define void @usually_taken(
; ALL: call void @escape(
define void @usually_taken(i1 %take, i1 %use) sanitize_memtag {
  br i1 %take, label %call, label %done, !prof !1
call:
  call void @worker(i1 %use)
  br label %done
done:
  ret void
}

; ALL-LABEL: define void @specialized(
; ALL-NOT: call void @worker(
; ALL: ret void
define void @specialized(i1 %take) sanitize_memtag {
  br i1 %take, label %call, label %done, !prof !0
call:
  call void @worker(i1 false)
  br label %done
done:
  ret void
}

; ALL-LABEL: define void @forced(
; ALL: call void @escape(
define void @forced(i1 %take, i1 %use) sanitize_memtag {
  br i1 %take, label %call, label %done, !prof !0
call:
  call void @worker(i1 %use) #0
  br label %done
done:
  ret void
}

; An entire lifetime inside a single block can acquire and release the slot
; on the path that actually uses it. Keep the ordinary inline budget.
define internal void @scoped_worker(i1 %use) sanitize_memtag {
entry:
  %slot = alloca i8
  br i1 %use, label %work, label %done
work:
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @escape(ptr %slot)
  call void @escape(ptr %slot)
  call void @escape(ptr %slot)
  call void @llvm.lifetime.end.p0(ptr %slot)
  br label %done
done:
  ret void
}

; ALL-LABEL: define void @scoped(
; ALL: call void @escape(
define void @scoped(i1 %take, i1 %use) sanitize_memtag {
  br i1 %take, label %call, label %done, !prof !0
call:
  call void @scoped_worker(i1 %use)
  br label %done
done:
  ret void
}

attributes #0 = { alwaysinline }
!0 = !{!"branch_weights", i32 1, i32 3}
!1 = !{!"branch_weights", i32 3, i32 1}
