;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; timer.cancel. Disarm owned timer and notify waiters.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose timer.cancel
  ;; and the grant must authorize timer.cancel. Applicable grant purposes include timer.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the timer.cancel action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `timer` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "timer.cancel" (func $wr_timer_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; timer.create. Clock dependency needs independent read grant.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose timer.create
  ;; and the grant must authorize timer.create. Applicable grant purposes include timer. Depending on
  ;; the selected inputs and plan, the VM also checks clock.read.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the timer.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `clock_capability`
  ;;   (`u64`), `clock` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `resource` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "timer.create" (func $wr_timer_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; timer.reset. Overflow-checked schedule; zero period is one-shot.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose timer.reset
  ;; and the grant must authorize timer.reset. Applicable grant purposes include timer.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the timer.reset action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `timer` (`u64`),
  ;;   `due` (`i64`), `period` (`i64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "timer.reset" (func $wr_timer_reset (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; timer.take. Coalesced occurrence record consumed only after delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose timer.take
  ;; and the grant must authorize timer.take. Applicable grant purposes include timer.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the timer.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `timer` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `expected` (`i64`),
  ;;   `actual` (`i64`), `occurrences` (`u64`), `clock_epoch` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "timer.take" (func $wr_timer_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "timer.cancel" (func $wr_timer_cancel))
  (export "timer.create" (func $wr_timer_create))
  (export "timer.reset" (func $wr_timer_reset))
  (export "timer.take" (func $wr_timer_take))
)
