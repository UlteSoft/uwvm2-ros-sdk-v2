;; Read the version from the VM's ROS scene and verify a signed scale conversion.
(module
  (import "uwvm_ros_v2" "abi" (func $abi (result i32)))
  (func $millimetres (param $metres i32) (result i32)
    (i32.mul (local.get $metres) (i32.const 1000)))
  (func (export "_start")
    (if (i32.ne (call $abi) (i32.const 2)) (then unreachable))
    (if (i32.ne (call $millimetres (i32.const -3)) (i32.const -3000)) (then unreachable))))
