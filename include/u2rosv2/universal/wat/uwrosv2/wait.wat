;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; wait.acknowledge. Acknowledge source sequence; readiness is not data consumption.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; wait.acknowledge and the grant must authorize wait.acknowledge. Applicable grant purposes
  ;; include wait.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the wait.acknowledge action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `waitset` (`u64`),
  ;;   `source` (`u64`), `sequence` (`u64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "wait.acknowledge" (func $wr_wait_acknowledge (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; wait.add. Source requires independent resource.observe; bounded membership.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose wait.add and
  ;; the grant must authorize wait.add. Applicable grant purposes include wait. Depending on the
  ;; selected inputs and plan, the VM also checks resource.observe.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the wait.add action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `waitset` (`u64`),
  ;;   `source_capability` (`u64`), `source` (`u64`), `interests` (`u64`), `token` (`u64`).
  ;; @param $size - (i64) Exact request length, 40 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "wait.add" (func $wr_wait_add (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; wait.create. Create empty owned waitset.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose wait.create
  ;; and the grant must authorize wait.create. Applicable grant purposes include wait.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the wait.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the checked zero-length request range.
  ;; @param $size - (i64) Exact request length, 0 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `resource` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "wait.create" (func $wr_wait_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; wait.poll. Nonconsuming bounded readiness; infinite wait explicit; authority revalidated after
  ;; wake.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose wait.poll and
  ;; the grant must authorize wait.poll. Applicable grant purposes include wait.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the wait.poll action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `waitset` (`u64`),
  ;;   `duration_ns` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `records`
  ;;   (`array<ready_record>`). Each 32-byte record contains source, token, events and sequence, with
  ;;   no array length prefix.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "wait.poll" (func $wr_wait_poll (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; wait.remove. Detach exact source from owned waitset.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose wait.remove
  ;; and the grant must authorize wait.remove. Applicable grant purposes include wait.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the wait.remove action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `waitset` (`u64`),
  ;;   `source` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "wait.remove" (func $wr_wait_remove (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "wait.acknowledge" (func $wr_wait_acknowledge))
  (export "wait.add" (func $wr_wait_add))
  (export "wait.create" (func $wr_wait_create))
  (export "wait.poll" (func $wr_wait_poll))
  (export "wait.remove" (func $wr_wait_remove))
)
