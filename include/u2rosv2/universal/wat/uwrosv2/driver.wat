;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; driver.connect. Perform one nonblocking handshake on a registered inherited channel. Readiness
  ;; grants no actuation authority; repeated handshake polling never launches code.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; driver.connect and the grant must authorize driver.connect. Applicable grant purposes include
  ;; driver.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the driver.connect action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the checked zero-length request range.
  ;; @param $size - (i64) Exact request length, 0 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `connected` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65552. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "driver.connect" (func $wr_driver_connect (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; driver.describe. Read detached session metadata only; never pump packets, infer physical safety,
  ;; restart a driver or replenish authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; driver.describe and the grant must authorize driver.describe. Applicable grant purposes include
  ;; driver.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the driver.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the checked zero-length request range.
  ;; @param $size - (i64) Exact request length, 0 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `state` (`u64`),
  ;;   `sequence` (`u64`), `status` (`u64`), `effect_unknown` (`bool`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65552. The
  ;;   fixed result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "driver.describe" (func $wr_driver_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; driver.disconnect. Release this connection and erase retained buffers. Best-effort release and
  ;; local descriptor closure never terminate a shared driver. Independent receiver expiry remains
  ;; mandatory.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; driver.disconnect and the grant must authorize driver.disconnect. Applicable grant purposes
  ;; include driver.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the driver.disconnect action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the checked zero-length request range.
  ;; @param $size - (i64) Exact request length, 0 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `released` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65552. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "driver.disconnect" (func $wr_driver_disconnect (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; driver.result. Receive an exact sequence and incarnation-bound result. Failed guest delivery
  ;; retains bytes. Timeout after send fences the session with effect_unknown; never retry a
  ;; non-idempotent operation automatically.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose driver.result
  ;; and the grant must authorize driver.result. Applicable grant purposes include driver.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the driver.result action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `sequence` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `status` (`u64`),
  ;;   `payload` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65552. Reserve
  ;;   16 bytes plus the route's configured maximum response payload even when the pending response
  ;;   is shorter.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. The response record contains the driver's status and payload.
  (import "uwvm_ros_v2" "driver.result" (func $wr_driver_result (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; driver.submit. Submit one bounded fixed-contract request. Exact in-flight retry returns its
  ;; receipt without resending. Changed bytes or deadline conflict; submission is local transport
  ;; acceptance, never physical completion.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose driver.submit
  ;; and the grant must authorize driver.submit. Applicable grant purposes include driver.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the driver.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `sequence` (`u64`),
  ;;   `deadline` (`u64`), `payload` (`bytes`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   65560 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `sequence` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65552. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "driver.submit" (func $wr_driver_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "driver.connect" (func $wr_driver_connect))
  (export "driver.describe" (func $wr_driver_describe))
  (export "driver.disconnect" (func $wr_driver_disconnect))
  (export "driver.result" (func $wr_driver_result))
  (export "driver.submit" (func $wr_driver_submit))
)
