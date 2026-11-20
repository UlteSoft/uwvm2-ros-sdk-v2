;; @brief Port ROS Noetic Costmap2D's unsigned row-major index.
;; @details Callers provide in-bounds coordinates when using an index to access a grid.
(module
  (func $cell (export "cell_index") (param $width i32) (param $column i32) (param $row i32) (result i32)
    (i32.add (i32.mul (local.get $row) (local.get $width)) (local.get $column)))
  (func (export "_start")
    (if (i32.ne (call $cell (i32.const 400) (i32.const 7) (i32.const 3)) (i32.const 1207))
      (then unreachable))
    (if (i32.ne (call $cell (i32.const 17) (i32.const 16) (i32.const 0)) (i32.const 16))
      (then unreachable))
    (if (i32.ne (call $cell (i32.const 17) (i32.const 0) (i32.const 1)) (i32.const 17))
      (then unreachable))
    (if (i32.ne (call $cell (i32.const -1) (i32.const 7) (i32.const 2)) (i32.const 5))
      (then unreachable))))
