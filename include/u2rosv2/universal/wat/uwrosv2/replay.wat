;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; replay.open. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
  ;; caller incarnation ownership, atomic source read/export authority and retained pinned objects.
  ;; Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only
  ;; and never publishes or changes clocks.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose replay.open
  ;; and the grant must authorize replay.open. Applicable grant purposes include replay. Depending on
  ;; the selected inputs and plan, the VM also checks resource.observe, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the replay.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `source_capability`
  ;;   (`u64`), `profile` (`profile`), `objects` (`array<recording_object>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   6072 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `replay` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "replay.open" (func $wr_replay_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; replay.read. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
  ;; caller incarnation ownership, atomic source read/export authority and retained pinned objects.
  ;; Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only
  ;; and never publishes or changes clocks.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose replay.read
  ;; and the grant must authorize replay.read. Applicable grant purposes include replay. Depending on
  ;; the selected inputs and plan, the VM also checks resource.observe, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the replay.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `replay` (`u64`),
  ;;   `limit` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `ordinal` (`u64`),
  ;;   `records` (`array<recording_message>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "replay.read" (func $wr_replay_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; replay.seek. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
  ;; caller incarnation ownership, atomic source read/export authority and retained pinned objects.
  ;; Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only
  ;; and never publishes or changes clocks.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose replay.seek
  ;; and the grant must authorize replay.seek. Applicable grant purposes include replay. Depending on
  ;; the selected inputs and plan, the VM also checks resource.observe, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the replay.seek action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `replay` (`u64`),
  ;;   `ordinal` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `ordinal` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "replay.seek" (func $wr_replay_seek (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "replay.open" (func $wr_replay_open))
  (export "replay.read" (func $wr_replay_read))
  (export "replay.seek" (func $wr_replay_seek))
)
