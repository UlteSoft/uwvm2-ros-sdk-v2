;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; artifact.abort. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.abort and the grant must authorize artifact.abort. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.abort action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `object` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.abort" (func $wr_artifact_abort (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.append. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.append and the grant must authorize artifact.append. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.append action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `object` (`u64`), `expected_offset` (`u64`), `data` (`bytes`).
  ;; @param $size - (i64) 24 bytes of header plus the raw data byte count, at most 4194328 bytes in
  ;;   total. The data has no length prefix.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.append" (func $wr_artifact_append (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.begin. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.begin and the grant must authorize artifact.begin. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.begin action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `reservation` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.begin" (func $wr_artifact_begin (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.commit. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.commit and the grant must authorize artifact.commit. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.commit action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `object` (`u64`), `expected_size` (`u64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.commit" (func $wr_artifact_commit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.describe. 64-byte approved metadata: four LE words then raw32 SHA256. Purpose codes1
  ;; package,2 configuration,3 calibration,4 map,5 model-weights. No source path or FD.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.describe and the grant must authorize artifact.describe. Applicable grant purposes
  ;; include package, configuration, calibration, map, model-weights.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `object` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `generation` (`u64`),
  ;;   `size` (`u64`), `purpose_code` (`u64`), `maximum_transfer` (`u64`), `sha256` (`bytes`). The
  ;;   last 32 bytes are the raw SHA-256 digest.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 64 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "artifact.describe" (func $wr_artifact_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.open. Exact positive deployment generation and 32 raw SHA256 bytes; sealed-input
  ;; binding only. Roll back unpublished handles on failed delivery. No output-store read binding.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose artifact.open
  ;; and the grant must authorize artifact.open. Applicable grant purposes include package,
  ;; configuration, calibration, map, model-weights.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `generation`
  ;;   (`u64`), `sha256` (`bytes`). The SHA-256 digest occupies 32 raw bytes immediately after the
  ;;   generation.
  ;; @param $size - (i64) Exact request length, 40 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "artifact.open" (func $wr_artifact_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.publish. Publish one complete bounded volatile object using the existing exact replay
  ;; stream; all publish/begin/append/commit rights and exposures required; scratch capacity reserved
  ;; before carrier copying.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.publish and the grant must authorize artifact.publish. Applicable grant purposes
  ;; include cache. Depending on the selected inputs and plan, the VM also checks artifact.begin,
  ;; artifact.append, artifact.commit.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.publish action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `size` (`u64`), `data` (`bytes`).
  ;; @param $size - (i64) 16 bytes of header plus the declared number of raw data bytes. The header
  ;;   check bounds the whole span at 4194328 bytes and the grant additionally bounds the payload.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.publish" (func $wr_artifact_publish (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.read. Bounded requested bytes from immutable handle and offset; raw output, EOF short
  ;; read, no cursor. Exact read action; requested bytes cannot exceed configured transfer or output
  ;; capacity. Published volatile cache objects are also readable under independent cache read
  ;; authority; staging stays hidden.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose artifact.read
  ;; and the grant must authorize artifact.read. Applicable grant purposes include package,
  ;; configuration, calibration, map, model-weights, cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `object` (`u64`),
  ;;   `offset` (`u64`), `bytes` (`u64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `data` (`bytes`). The
  ;;   result contains raw data without a length prefix.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "artifact.read" (func $wr_artifact_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.receipt. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.receipt and the grant must authorize artifact.receipt. Applicable grant purposes
  ;; include cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.receipt action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.receipt" (func $wr_artifact_receipt (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.remove. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.remove and the grant must authorize artifact.remove. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.remove action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `object` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.remove" (func $wr_artifact_remove (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; artifact.status. Explicit cache/volatile-output only. Per-alias next-key ACK and exact
  ;; last-request replay; full begin allocation remains charged until abort/remove. Publication is
  ;; immutable session data, never durable. Status and receipt queries do not acknowledge. No host
  ;; path or descriptor.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; artifact.status and the grant must authorize artifact.status. Applicable grant purposes include
  ;; cache.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the artifact.status action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `object` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `operation` (`u64`), `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`),
  ;;   `total_bytes` (`u64`), `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 72 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "artifact.status" (func $wr_artifact_status (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "artifact.abort" (func $wr_artifact_abort))
  (export "artifact.append" (func $wr_artifact_append))
  (export "artifact.begin" (func $wr_artifact_begin))
  (export "artifact.commit" (func $wr_artifact_commit))
  (export "artifact.describe" (func $wr_artifact_describe))
  (export "artifact.open" (func $wr_artifact_open))
  (export "artifact.publish" (func $wr_artifact_publish))
  (export "artifact.read" (func $wr_artifact_read))
  (export "artifact.receipt" (func $wr_artifact_receipt))
  (export "artifact.remove" (func $wr_artifact_remove))
  (export "artifact.status" (func $wr_artifact_status))
)
