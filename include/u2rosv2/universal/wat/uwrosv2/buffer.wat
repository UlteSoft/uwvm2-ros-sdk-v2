;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; buffer.create. Reserve bounded data/workspace before publication.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose buffer.create
  ;; and the grant must authorize buffer.create. Applicable grant purposes include buffer.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the buffer.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `layout`
  ;;   (`buffer_layout`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194328 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "buffer.create" (func $wr_buffer_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; buffer.describe. Untrusted origin cannot be relabelled as a trusted sensor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; buffer.describe and the grant must authorize buffer.describe. Applicable grant purposes include
  ;; buffer.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the buffer.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `layout`
  ;;   (`buffer_layout`), `sealed` (`bool`), `provenance` (`text`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "buffer.describe" (func $wr_buffer_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; buffer.read. Exact bounded read; no host descriptor export.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose buffer.read
  ;; and the grant must authorize buffer.read. Applicable grant purposes include buffer.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the buffer.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `offset` (`u64`), `bytes` (`u64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `data` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "buffer.read" (func $wr_buffer_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; buffer.seal. Immutable publication with digest and registered layout.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose buffer.seal
  ;; and the grant must authorize buffer.seal. Applicable grant purposes include buffer.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the buffer.seal action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `digest` (`bytes`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194328 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `reference`
  ;;   (`buffer_ref`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816. The
  ;;   fixed result occupies 16 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "buffer.seal" (func $wr_buffer_seal (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; buffer.write. Contiguous bounded write only before seal; no native pointer.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose buffer.write
  ;; and the grant must authorize buffer.write. Applicable grant purposes include buffer.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the buffer.write action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `expected_offset` (`u64`), `data` (`bytes`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194328 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `accepted_bytes`
  ;;   (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "buffer.write" (func $wr_buffer_write (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "buffer.create" (func $wr_buffer_create))
  (export "buffer.describe" (func $wr_buffer_describe))
  (export "buffer.read" (func $wr_buffer_read))
  (export "buffer.seal" (func $wr_buffer_seal))
  (export "buffer.write" (func $wr_buffer_write))
)
