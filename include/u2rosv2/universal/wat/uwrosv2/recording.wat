;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; recording.append. Private finite volatile MCAP store with exact deployment channel/buffer
  ;; profiles, caller incarnation ownership, atomic source read/export authority and retained pinned
  ;; objects. Writer mutations use next-key exact recovery; resource.close releases writer or an
  ;; unpinned checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; recording.append and the grant must authorize recording.append. Applicable grant purposes
  ;; include recording. Depending on the selected inputs and plan, the VM also checks buffer.read,
  ;; data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the recording.append action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `writer` (`u64`),
  ;;   `key` (`u64`), `items` (`array<recording_buffer_item>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   6072 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`recording_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 104 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "recording.append" (func $wr_recording_append (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; recording.checkpoint. Private finite volatile MCAP store with exact deployment channel/buffer
  ;; profiles, caller incarnation ownership, atomic source read/export authority and retained pinned
  ;; objects. Writer mutations use next-key exact recovery; resource.close releases writer or an
  ;; unpinned checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; recording.checkpoint and the grant must authorize recording.checkpoint. Applicable grant
  ;; purposes include recording.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the recording.checkpoint action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `writer` (`u64`),
  ;;   `key` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`recording_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 104 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "recording.checkpoint" (func $wr_recording_checkpoint (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; recording.open. Private finite volatile MCAP store with exact deployment channel/buffer
  ;; profiles, caller incarnation ownership, atomic source read/export authority and retained pinned
  ;; objects. Writer mutations use next-key exact recovery; resource.close releases writer or an
  ;; unpinned checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; recording.open and the grant must authorize recording.open. Applicable grant purposes include
  ;; recording.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the recording.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   6072 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `writer` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "recording.open" (func $wr_recording_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; recording.stop. Private finite volatile MCAP store with exact deployment channel/buffer
  ;; profiles, caller incarnation ownership, atomic source read/export authority and retained pinned
  ;; objects. Writer mutations use next-key exact recovery; resource.close releases writer or an
  ;; unpinned checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; recording.stop and the grant must authorize recording.stop. Applicable grant purposes include
  ;; recording.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the recording.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `writer` (`u64`),
  ;;   `key` (`u64`), `drain` (`bool`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`recording_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 104 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "recording.stop" (func $wr_recording_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "recording.append" (func $wr_recording_append))
  (export "recording.checkpoint" (func $wr_recording_checkpoint))
  (export "recording.open" (func $wr_recording_open))
  (export "recording.stop" (func $wr_recording_stop))
)
