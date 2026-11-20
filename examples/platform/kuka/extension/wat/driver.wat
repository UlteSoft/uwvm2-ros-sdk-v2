;; @brief Verify platform and parent grant denial on the private Xmake test channel.
;; @details Three byte alias at 0, capability at 8, reply at 16, written count at 24.
(module
  (import "uwvm_ros_v2" "capability.open" (func $open (param i32 i64 i64 i64) (result i32)))
  (import "uwvm_ros_v2" "capability.close" (func $close (param i64) (result i32)))
  (import "uwvm_ros_v2" "driver.connect" (func $connect (param i64 i32 i64 i64 i64 i64 i64) (result i32)))
  (memory 1 1)
  (data (i32.const 0) "arm")
  (func (export "_start")
    (local $handle i64)
    (i64.store (i32.const 16) (i64.const 0x4321))
    (i64.store (i32.const 24) (i64.const 0x1234))
    (if (call $open (i32.const 0) (i64.const 0) (i64.const 3) (i64.const 8)) (then unreachable))
    (local.set $handle (i64.load (i32.const 8)))
    (if (i32.ne
          (call $connect (local.get $handle) (i32.const 0) (i64.const 0) (i64.const 0)
                         (i64.const 16) (i64.const 8) (i64.const 24))
          (i32.const 13))
      (then unreachable))
    (if (i64.ne (i64.load (i32.const 16)) (i64.const 0x4321)) (then unreachable))
    (if (i64.ne (i64.load (i32.const 24)) (i64.const 0x1234)) (then unreachable))
    (if (call $close (local.get $handle)) (then unreachable))))
