;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; lifecycle.open. Open one explicitly permitted client=1/server=2 role in a deployed
  ;; local-lifecycle alias; no native node or actuator authority. Opening never resets state or
  ;; history.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.open and the grant must authorize lifecycle.open. Applicable grant purposes include
  ;; lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `role` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.open" (func $wr_lifecycle_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; lifecycle.respond. Resolve only an exactly delivered matching request/generation using ROS
  ;; outcome97/98/99. Preserve last exact response receipt; error queues error-processing callback.
  ;; No native callback execution.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.respond and the grant must authorize lifecycle.respond. Applicable grant purposes
  ;; include lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.respond action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `handle` (`u64`),
  ;;   `request` (`u64`), `expected_generation` (`u64`), `outcome` (`u64`).
  ;; @param $size - (i64) Exact request length, 32 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `request` (`u64`), `generation` (`u64`), `state` (`u64`), `status` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 40 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.respond" (func $wr_lifecycle_respond (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; lifecycle.state. Observe owned cached logical state and enforce an expired finite deadline on
  ;; access; no physical or autonomous stop guarantee.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.state and the grant must authorize lifecycle.state. Applicable grant purposes include
  ;; lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.state action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `handle` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `state` (`u64`),
  ;;   `generation` (`u64`), `request` (`u64`), `transition` (`u64`), `deadline` (`u64`), `status`
  ;;   (`u64`), `delivered` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 56 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.state" (func $wr_lifecycle_state (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; lifecycle.submit. Exactly ordered successful-submission keys with original receipt replay,
  ;; finite absolute steady deadline, expected generation and one pending callback. Rejected
  ;; submissions do not consume key.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.submit and the grant must authorize lifecycle.submit. Applicable grant purposes
  ;; include lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.submit action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `handle` (`u64`),
  ;;   `key` (`u64`), `transition` (`u64`), `expected_generation` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Exact request length, 40 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `request` (`u64`), `generation` (`u64`), `state` (`u64`), `status` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 40 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.submit" (func $wr_lifecycle_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; lifecycle.take. Reserve one callback, release provider lock before checked delivery, then
  ;; revalidate owner/request/generation/deadline before marking delivered. Failed delivery is not
  ;; consumed.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.take and the grant must authorize lifecycle.take. Applicable grant purposes include
  ;; lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `handle` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `request` (`u64`),
  ;;   `transition` (`u64`), `generation` (`u64`), `phase` (`u64`), `deadline` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 40 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.take" (func $wr_lifecycle_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; lifecycle.transitions. Return only currently legal and deployment-permitted transition bits; no
  ;; transition authority is granted.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; lifecycle.transitions and the grant must authorize lifecycle.transitions. Applicable grant
  ;; purposes include lifecycle.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the lifecycle.transitions action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `handle` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `allowed_mask`
  ;;   (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "lifecycle.transitions" (func $wr_lifecycle_transitions (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "lifecycle.open" (func $wr_lifecycle_open))
  (export "lifecycle.respond" (func $wr_lifecycle_respond))
  (export "lifecycle.state" (func $wr_lifecycle_state))
  (export "lifecycle.submit" (func $wr_lifecycle_submit))
  (export "lifecycle.take" (func $wr_lifecycle_take))
  (export "lifecycle.transitions" (func $wr_lifecycle_transitions))
)
