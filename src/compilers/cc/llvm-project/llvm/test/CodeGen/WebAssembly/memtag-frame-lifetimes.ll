; RUN: split-file %s %t
; RUN: llc %t/frame.ll -mtriple=wasm32 -mattr=+memtag,+atomics,+bulk-memory -wasm-memtag-private-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=PRIVATE -DW=32
; RUN: llc %t/frame.ll -mtriple=wasm64 -mattr=+memtag,+atomics,+bulk-memory -wasm-memtag-private-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=PRIVATE -DW=64
; RUN: llc %t/frame.ll -mtriple=wasm32 -mattr=+memtag,+atomics,+bulk-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=SHARED
; RUN: llc %t/frame.ll -mtriple=wasm64 -mattr=+memtag,+atomics,+bulk-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=SHARED
; RUN: cat %t/frame.ll %t/private-flag | llc -mtriple=wasm32 -mattr=+memtag,+atomics,+bulk-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=PRIVATE -DW=32
; RUN: cat %t/frame.ll %t/shared-flag | llc -mtriple=wasm32 -mattr=+memtag,+atomics,+bulk-memory -wasm-memtag-private-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefixes=SHARED,REQUIRED
; RUN: llc %t/explicit.ll -mtriple=wasm32 -mattr=+memtag -wasm-memtag-private-memory -stop-after=wasm-stack-tagging -o - | FileCheck %s --check-prefix=EXPLICIT

;--- frame.ll
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.memset.p0.i32(ptr, i8, i32, i1 immarg)
declare ptr @llvm.stacksave.p0()
declare void @llvm.stackrestore.p0(ptr)
declare i32 @llvm.eh.sjlj.setjmp(ptr)
declare i32 @__gxx_wasm_personality_v0(...)
declare void @observe(ptr)
declare void @observe_pair(ptr, ptr)
declare void @callee() nounwind

; Allocas and their starts are deliberately in opposite orders. The private
; store in the prologue addresses the complete pointer slot after its start.
; The variable index, observable call and load must all use their live tags.
; PRIVATE-LABEL: define void @pair(
; PRIVATE: %buffer = alloca
; PRIVATE-NEXT: %out = alloca
; PRIVATE-NEXT: [[OUT:%[^ ]+]] = call ptr @llvm.wasm.memtag.claim.i[[W]](i32 0, ptr %out, i[[W]] 16), !dbg ![[START:[0-9]+]]
; PRIVATE-NEXT: store ptr null, ptr [[OUT]]
; PRIVATE-NEXT: [[BUF:%[^ ]+]] = call ptr @llvm.wasm.memtag.claim.i[[W]](i32 0, ptr %buffer, i[[W]] 32), !dbg ![[BUFSTART:[0-9]+]]
; PRIVATE-NEXT: call void @llvm.memset.p0.i32(ptr [[BUF]], i8 0, i32 32, i1 false)
; PRIVATE: %byte = getelementptr i8, ptr [[BUF]], i32 %index
; PRIVATE-NEXT: store volatile i8 7, ptr %byte, align 1, !dbg ![[STORE:[0-9]+]]
; PRIVATE: call void @observe_pair(ptr [[BUF]], ptr [[OUT]])
; PRIVATE-NEXT: %p = load volatile ptr, ptr [[OUT]]
; PRIVATE-NEXT: call void @observe(ptr %p)
; PRIVATE: done:
; PRIVATE-NEXT: {{%[^ ]+}} = call ptr @llvm.wasm.memtag.release.i[[W]](i32 0, ptr [[BUF]], i[[W]] 32), !dbg ![[END:[0-9]+]]
; PRIVATE-NEXT: {{%[^ ]+}} = call ptr @llvm.wasm.memtag.release.i[[W]](i32 0, ptr [[OUT]], i[[W]] 16), !dbg ![[END]]
; PRIVATE-NEXT: ret void
; SHARED-LABEL: define void @pair(
; SHARED: call ptr @llvm.wasm.memtag.reserve.
; SHARED: call ptr @llvm.wasm.memtag.reserve.
; SHARED: call ptr @llvm.wasm.memtag.activate.
; SHARED: call ptr @llvm.wasm.memtag.activate.
; SHARED: done:
; SHARED: call ptr @llvm.wasm.memtag.release.
; SHARED-NEXT: {{.*}}call ptr @llvm.wasm.memtag.reserve.
define void @pair(i1 %enter, i1 %again, i32 %index) nounwind sanitize_memtag !dbg !4 {
entry:
  %buffer = alloca [32 x i8], align 16
  %out = alloca ptr, align 16
  call void @llvm.lifetime.start.p0(ptr %out), !dbg !7
  store ptr null, ptr %out, align 4, !dbg !7
  call void @llvm.lifetime.start.p0(ptr %buffer), !dbg !8
  call void @llvm.memset.p0.i32(ptr %buffer, i8 0, i32 32, i1 false), !dbg !8
  br i1 %enter, label %work, label %done, !dbg !8
work:
  %byte = getelementptr i8, ptr %buffer, i32 %index, !dbg !9
  store volatile i8 7, ptr %byte, align 1, !dbg !9
  call void @observe_pair(ptr %buffer, ptr %out), !dbg !9
  %p = load volatile ptr, ptr %out, align 4, !dbg !9
  call void @observe(ptr %p), !dbg !9
  br i1 %again, label %work, label %done, !dbg !9
done:
  call void @llvm.lifetime.end.p0(ptr %buffer), !dbg !10
  call void @llvm.lifetime.end.p0(ptr %out), !dbg !10
  ret void, !dbg !10
}

; An external call before the start can observe a pending registration.
; PRIVATE-LABEL: define void @published_before(
; PRIVATE: [[PENDING:%[^ ]+]] = call ptr @llvm.wasm.memtag.reserve.
; PRIVATE-NEXT: call void @observe(ptr [[PENDING]])
; PRIVATE-NEXT: [[LIVE:%[^ ]+]] = call ptr @llvm.wasm.memtag.activate.
; PRIVATE-NEXT: call void @observe(ptr [[LIVE]])
define void @published_before() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @observe(ptr %slot)
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}

; An address used after the end must keep its pending generation.
; PRIVATE-LABEL: define void @published_after(
; PRIVATE: done:
; PRIVATE: [[BASE:%[^ ]+]] = call ptr @llvm.wasm.memtag.release.
; PRIVATE-NEXT: [[DEAD:%[^ ]+]] = call ptr @llvm.wasm.memtag.reserve.i[[W]](i32 0, ptr [[BASE]],
; PRIVATE-NEXT: call void @observe(ptr [[DEAD]])
; PRIVATE-NEXT: {{.*}}call ptr @llvm.wasm.memtag.release.i[[W]](i32 0, ptr [[DEAD]],
define void @published_after() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  call void @observe(ptr %slot)
  ret void
}

; A direct return uses the address after the end. A GEP captured while live
; retains its issued generation at return even though its extent is retired.
; PRIVATE-LABEL: define ptr @return_dead(
; PRIVATE: done:
; PRIVATE: [[NEW:%[^ ]+]] = call ptr @llvm.wasm.memtag.reserve.
; PRIVATE-NEXT: {{.*}}call ptr @llvm.wasm.memtag.release.i[[W]](i32 0, ptr [[NEW]],
; PRIVATE-NEXT: ret ptr [[NEW]]
define ptr @return_dead() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret ptr %slot
}
; PRIVATE-LABEL: define ptr @return_captured(
; PRIVATE: [[TAG:%[^ ]+]] = call ptr @llvm.wasm.memtag.claim.
; PRIVATE-NEXT: %captured = getelementptr i8, ptr [[TAG]], i32 1
; PRIVATE: done:
; PRIVATE-NEXT: {{.*}}call ptr @llvm.wasm.memtag.release.i[[W]](i32 0, ptr [[TAG]],
; PRIVATE-NEXT: ret ptr %captured
define ptr @return_captured() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  %captured = getelementptr i8, ptr %slot, i32 1
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret ptr %captured
}

; A bypass or repeated start needs a changing token.
; PRIVATE-LABEL: define void @conditional_loop(
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
; PRIVATE: call ptr @llvm.wasm.memtag.activate.
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.release.
define void @conditional_loop(i1 %active, i1 %again) nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  br i1 %active, label %start, label %done
start:
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br i1 %again, label %start, label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}

; A second return must release exactly the owner on its own path.
; PRIVATE-LABEL: define void @two_returns(
; PRIVATE: early:
; PRIVATE-NEXT: {{.*}}call ptr @llvm.wasm.memtag.release.
; PRIVATE-NEXT: ret void
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
define void @two_returns(i1 %skip) nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br i1 %skip, label %early, label %done
early:
  ret void
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}

; Stack restoration and musttail retirement keep their existing schedules.
; PRIVATE-LABEL: define void @restore_stack(
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
define void @restore_stack() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  %sp = call ptr @llvm.stacksave.p0()
  call void @observe(ptr %slot)
  call void @llvm.stackrestore.p0(ptr %sp)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}
; PRIVATE-LABEL: define void @tail(
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
; PRIVATE-NEXT: {{.*}}call ptr @llvm.wasm.memtag.release.
; PRIVATE-NEXT: musttail call void @callee()
define void @tail() nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  musttail call void @callee()
  ret void
}

; Unusual control flow and personality-bearing frames keep their full owner.
; PRIVATE-LABEL: define i32 @sjlj(
; PRIVATE: call i32 @llvm.eh.sjlj.setjmp
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
define i32 @sjlj(ptr %env) nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  %result = call i32 @llvm.eh.sjlj.setjmp(ptr %env)
  call void @observe(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret i32 %result
}
; PRIVATE-LABEL: define void @personality(
; PRIVATE: done:
; PRIVATE: call ptr @llvm.wasm.memtag.reserve.
define void @personality() nounwind sanitize_memtag personality ptr @__gxx_wasm_personality_v0 {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}

; PRIVATE-DAG: !"wasm-feature-shared-mem", i32 45
; PRIVATE-DAG: ![[START]] = !DILocation(line: 3,
; PRIVATE-DAG: ![[BUFSTART]] = !DILocation(line: 4,
; PRIVATE-DAG: ![[STORE]] = !DILocation(line: 7,
; PRIVATE-DAG: ![[END]] = !DILocation(line: 9,
; REQUIRED: !"wasm-feature-shared-mem", i32 43
!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!1}
!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !2, producer: "test", isOptimized: true, runtimeVersion: 0, emissionKind: FullDebug)
!1 = !{i32 2, !"Debug Info Version", i32 3}
!2 = !DIFile(filename: "frame.c", directory: "/")
!3 = !DISubroutineType(types: !5)
!4 = distinct !DISubprogram(name: "pair", scope: !2, file: !2, line: 2, type: !3, scopeLine: 2, spFlags: DISPFlagDefinition, unit: !0)
!5 = !{}
!7 = !DILocation(line: 3, column: 1, scope: !4)
!8 = !DILocation(line: 4, column: 1, scope: !4)
!9 = !DILocation(line: 7, column: 2, scope: !4)
!10 = !DILocation(line: 9, column: 1, scope: !4)

;--- private-flag
!llvm.module.flags = !{!11}
!11 = !{i32 1, !"wasm-feature-shared-mem", i32 45}

;--- shared-flag
!llvm.module.flags = !{!11}
!11 = !{i32 1, !"wasm-feature-shared-mem", i32 43}

;--- explicit.ll
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare ptr @llvm.wasm.memtag.reserve.i32(i32 immarg, ptr, i32)
declare ptr @llvm.wasm.memtag.activate.i32(i32 immarg, ptr, i32)
declare ptr @llvm.wasm.memtag.release.i32(i32 immarg, ptr, i32)
declare void @observe(ptr)
; EXPLICIT-LABEL: define void @explicit_owners(
; EXPLICIT: %pending = call ptr @llvm.wasm.memtag.reserve.i32(i32 0, ptr %other, i32 32)
; EXPLICIT-NEXT: %active = call ptr @llvm.wasm.memtag.activate.i32(i32 0, ptr %pending, i32 32)
; EXPLICIT-NEXT: %parent = call ptr @llvm.wasm.memtag.release.i32(i32 0, ptr %active, i32 32)
; EXPLICIT: done:
; EXPLICIT: call ptr @llvm.wasm.memtag.reserve.
define void @explicit_owners(ptr %other) nounwind sanitize_memtag {
entry:
  %slot = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %slot)
  call void @observe(ptr %slot)
  %pending = call ptr @llvm.wasm.memtag.reserve.i32(i32 0, ptr %other, i32 32)
  %active = call ptr @llvm.wasm.memtag.activate.i32(i32 0, ptr %pending, i32 32)
  %parent = call ptr @llvm.wasm.memtag.release.i32(i32 0, ptr %active, i32 32)
  br label %done
done:
  call void @llvm.lifetime.end.p0(ptr %slot)
  ret void
}
