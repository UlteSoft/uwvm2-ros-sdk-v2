;; @brief Scale a sample and query the exposed ROSv2 ABI from Core Wasm.
(module
  (import "uwvm_ros_v2" "abi" (func $abi (result i32)))
  (func $gain (export "gain") (param $sample i32) (param $scale i32) (param $offset i32) (result i32)
    (i32.add (i32.mul (local.get $sample) (local.get $scale)) (local.get $offset)))
  (func (export "_start")
    (if (i32.ne (call $abi) (i32.const 2)) (then unreachable))
    (if (i32.ne (call $gain (i32.const 9) (i32.const 4) (i32.const -1)) (i32.const 35))
      (then unreachable))))
