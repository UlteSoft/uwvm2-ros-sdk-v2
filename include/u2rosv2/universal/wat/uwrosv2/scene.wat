;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; abi. Returns major 2 only when explicitly exposed; errors encoded in same i32 result.
  ;;
  ;; The deployment must expose abi to the immediate caller.
  ;;
  ;; Call from the guest bound to this import. This signature has no guest memory operands.
  ;;
  ;; @returns The major ABI number (2) on success. The same i32 carries a scene status on failure.
  (import "uwvm_ros_v2" "abi" (func $wr_abi (result i32)))

  ;; action.cancel. Cancellation proposal for owned goal; broader cancel set requires separate
  ;; explicit scope.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose action.cancel
  ;; and the grant must authorize action.cancel. Applicable grant purposes include action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.cancel action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `client` (`u64`), `goal` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "action.cancel" (func $wr_action_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.cancel.set. Separately authorized finite explicit cancellation of owned goals. Whole-set
  ;; identity validation precedes native effects, each candidate has independent authority admission
  ;; and outcome evidence, and exact retry never reissues a candidate. Unknown stops further
  ;; attempts; no implicit wildcard or foreign-principal authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; action.cancel.set and the grant must authorize action.cancel.set. Applicable grant purposes
  ;; include action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.cancel.set action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `client` (`u64`), `selection` (`action_cancel_selection`), `deadline`
  ;;   (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `items` (`array<action_cancel_item>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "action.cancel.set" (func $wr_action_cancel_set (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.describe. Sanitized endpoint/owned-goal state and retention; no unrelated UUID discovery.
  ;; uwvm/action/State body follows action_endpoint_state.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; action.describe and the grant must authorize action.describe. Applicable grant purposes include
  ;; action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`),
  ;;   `goal` (`optional<u64>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `state` (`message`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "action.describe" (func $wr_action_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.open. Fix action role, goal/feedback/result types and retention. Creation is
  ;; asynchronous: explicit monotonically increasing key and finite absolute steady deadline;
  ;; response is a request receipt, not an endpoint. communication.open.take retrieves a separately
  ;; published typed handle.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose action.open
  ;; and the grant must authorize action.open. Applicable grant purposes include action. Depending on
  ;; the selected inputs and plan, the VM also checks node.open, type.describe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint`
  ;;   (`endpoint_request`), `creation_key` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "action.open" (func $wr_action_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.respond. Legal transition and exact secondary action checked; accepted cancel is not
  ;; terminal.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; action.respond and the grant must authorize action.respond. Applicable grant purposes include
  ;; action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.respond action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `endpoint` (`u64`), `response` (`action_response`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "action.respond" (func $wr_action_respond (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.submit. Goal UUID is correlated with owned goal resource; not a transferable authority
  ;; token.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose action.submit
  ;; and the grant must authorize action.submit. Applicable grant purposes include action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `client` (`u64`), `goal` (`goal`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "action.submit" (func $wr_action_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; action.take. Goal proposal/status/feedback/result/cancel request are distinct closed event
  ;; kinds. uwvm/action/Event body follows action_event; outer correlation is request, body goal/UUID
  ;; remain distinct.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose action.take
  ;; and the grant must authorize action.take. Applicable grant purposes include action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the action.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `record`
  ;;   (`delivery`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "action.take" (func $wr_action_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; bridge.create. Both endpoint directions/types/conversion/QoS preflight independently.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.create
  ;; and the grant must authorize bridge.create. Applicable grant purposes include bridge. Depending
  ;; on the selected inputs and plan, the VM also checks topic.reserve, topic.acknowledge,
  ;; topic.release, topic.describe, data.export, topic.publish.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `bridge`
  ;;   (`bridge_request`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "bridge.create" (func $wr_bridge_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.describe. Conversion/loss/QoS degradation/loop/correlation state only within scope.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; bridge.describe and the grant must authorize bridge.describe. Applicable grant purposes include
  ;; bridge.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `bridge` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `description`
  ;;   (`bridge_description`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "bridge.describe" (func $wr_bridge_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.start. Revalidate both grants and generation; no unchecked forwarding thread.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.start
  ;; and the grant must authorize bridge.start. Applicable grant purposes include bridge. Depending
  ;; on the selected inputs and plan, the VM also checks topic.reserve, topic.acknowledge,
  ;; topic.release, topic.describe, data.export, topic.publish.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.start action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `bridge` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "bridge.start" (func $wr_bridge_start (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.stop. Stop admitted direction, drain/cancel declared in profile.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.stop
  ;; and the grant must authorize bridge.stop. Applicable grant purposes include bridge.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `bridge` (`u64`), `profile` (`profile`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "bridge.stop" (func $wr_bridge_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; capability.close. Close capability handle without resetting budgets or resource lifetime.
  ;;
  ;; The caller must be an enrolled member of the handle's environment with capability.close exposed.
  ;;
  ;; Call from the guest bound to this import. This signature has no guest memory operands.
  ;;
  ;; @param $id - (i64) Handle issued by capability.open in the caller's environment.
  ;; @returns Zero retires the handle. BAD_HANDLE (9) identifies an unknown or already closed handle
  ;;   in the authorized environment.
  (import "uwvm_ros_v2" "capability.close" (func $wr_capability_close (param $id i64) (result i32)))

  ;; capability.open. Exact existing alias; no grant creation or upgrade; undelivered handle rolled
  ;; back.
  ;;
  ;; The caller must belong to an environment that exposes capability.open and grants the exact, live
  ;; alias.
  ;;
  ;; Keep the alias readable and the handle slot writable through the call. Their ranges may overlap.
  ;; The VM copies the alias before writing the handle. Preserve WasmMTE tags on both addresses.
  ;;
  ;; @param $memory - (i32) Index of the caller's linear memory containing both spans.
  ;; @param $offset - (i64) Guest address of the raw ASCII grant alias. Letters, digits, underscore,
  ;;   hyphen and period are allowed. The exact names `.` and `..` are invalid.
  ;; @param $size - (i64) Alias length from 1 through 255 bytes, excluding any terminator or wire
  ;;   prefix.
  ;; @param $output - (i64) Guest address of the writable eight-byte little-endian handle slot.
  ;; @returns Zero after writing the handle. Invalid alias bytes, invalid memory or failed handle
  ;;   delivery return INVALID (22). Failed delivery rolls back the unpublished handle. An absent or
  ;;   revoked alias returns DENIED (13).
  (import "uwvm_ros_v2" "capability.open" (func $wr_capability_open (param $memory i32) (param $offset i64) (param $size i64) (param $output i64) (result i32)))

  ;; capability.revoke. Permanently revoke exactly the carrier capability grant. The target must
  ;; equal the carrier capability, the exact grant must contain capability.revoke and the import must
  ;; be exposed. One pre-reserved receipt per grant retains the nonzero retry key, exact caller
  ;; incarnation and target. Atomically fence admissions before nonblocking provider retirement
  ;; notifications. Retirement state 1 means fenced with notification pending; 2 means local
  ;; notifications returned, never proof of native process exit, remote cancellation or physical
  ;; stop. Exact retry can recover failed output after revocation without repeating notifications or
  ;; allocating. Closing the handle or retiring the caller removes recovery access. No traffic quota
  ;; may prevent this independently authorized authority reduction; short output and cancellation
  ;; reject before fencing. Reopening cannot restore the grant; only trusted deployment creates new
  ;; authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; capability.revoke and the grant must authorize capability.revoke.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the capability.revoke action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key` (`u64`),
  ;;   `target_capability` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `key` (`u64`),
  ;;   `target_capability` (`u64`), `revocation_identity` (`u64`), `retirement_state` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "capability.revoke" (func $wr_capability_revoke (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; clock.create. Kind must match exact clock purpose.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose clock.create
  ;; and the grant must authorize clock.create. Applicable grant purposes include clock.steady,
  ;; clock.system, clock.ros.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the clock.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `kind` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `resource` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "clock.create" (func $wr_clock_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; clock.read. Sample owned clock; unstarted time remains flagged.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose clock.read
  ;; and the grant must authorize clock.read. Applicable grant purposes include clock.steady,
  ;; clock.system, clock.ros.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the clock.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `clock` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `now` (`i64`),
  ;;   `epoch` (`u64`), `started` (`bool`), `kind` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "clock.read" (func $wr_clock_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; clock.update. ROS clock source must independently permit clock.read with matching resource and
  ;; binding.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose clock.update
  ;; and the grant must authorize clock.update. Applicable grant purposes include clock.ros.
  ;; Depending on the selected inputs and plan, the VM also checks clock.read.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the clock.update action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `source_capability`
  ;;   (`u64`), `clock` (`u64`), `now` (`i64`), `started` (`bool`).
  ;; @param $size - (i64) Exact request length, 32 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "clock.update" (func $wr_clock_update (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; communication.open.cancel. Independent exact origin action and complete caller/incarnation
  ;; checks. Take publishes a typed endpoint only after fresh origin admission; cancelled/unknown
  ;; work retains native cleanup debt and never refunds creation work.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; communication.open.cancel and the grant must authorize communication.open.cancel. Applicable
  ;; grant purposes include node, topic, service, action. Depending on the selected inputs and plan,
  ;; the VM also checks node.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the communication.open.cancel action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "communication.open.cancel" (func $wr_communication_open_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; communication.open.take. Independent exact origin action and complete caller/incarnation checks.
  ;; Take publishes a typed endpoint only after fresh origin admission; cancelled/unknown work
  ;; retains native cleanup debt and never refunds creation work.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; communication.open.take and the grant must authorize communication.open.take. Applicable grant
  ;; purposes include node, topic, service, action. Depending on the selected inputs and plan, the VM
  ;; also checks node.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the communication.open.take action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`), `kind` (`u64`), `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 64 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "communication.open.take" (func $wr_communication_open_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; context.describe. Sanitized context identity, supported features and shutdown state. Provider
  ;; feature reporting distinguishes configured, native-attested supported and currently available
  ;; states; missing/failed native feature probes are not affirmative support.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; context.describe and the grant must authorize context.describe. Applicable grant purposes
  ;; include context.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the context.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `context` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `profile`
  ;;   (`profile`), `state` (`text`), `generation` (`u64`), `features` (`array<provider_feature>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "context.describe" (func $wr_context_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; context.open. Create an independently owned context only after complete provider/security
  ;; closure validation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose context.open
  ;; and the grant must authorize context.open. Applicable grant purposes include context.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the context.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "context.open" (func $wr_context_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; context.shutdown. Cancel owned work and wake waits; never process exit.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; context.shutdown and the grant must authorize context.shutdown. Applicable grant purposes
  ;; include context.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the context.shutdown action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `context` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "context.shutdown" (func $wr_context_shutdown (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; control.open. Reserve complete continuous cycle and safe-state contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose control.open
  ;; and the grant must authorize control.open. Applicable grant purposes include control. Depending
  ;; on the selected inputs and plan, the VM also checks device.submit, device.stop,
  ;; resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the control.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`), `device_capability` (`u64`), `device` (`u64`), `sources`
  ;;   (`array<control_source>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `opened`
  ;;   (`control_opening`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096. The fixed
  ;;   result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "control.open" (func $wr_control_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; control.result. Report actual execution, missed phase and watchdog outcome.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; control.result and the grant must authorize control.result. Applicable grant purposes include
  ;; control. Depending on the selected inputs and plan, the VM also checks device.submit,
  ;; device.stop, resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the control.result action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `cycle` (`u64`),
  ;;   `sequence` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "control.result" (func $wr_control_result (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; control.sample. A bounded input/read phase tied to write deadline and sequence.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; control.sample and the grant must authorize control.sample. Applicable grant purposes include
  ;; control. Depending on the selected inputs and plan, the VM also checks device.submit,
  ;; device.stop, resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the control.sample action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `cycle` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `sample`
  ;;   (`cycle_sample`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "control.sample" (func $wr_control_sample (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; control.stop. Drain or qualified safe stop; revoke never disables watchdog.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose control.stop
  ;; and the grant must authorize control.stop. Applicable grant purposes include control.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the control.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `cycle` (`u64`), `profile` (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "control.stop" (func $wr_control_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; control.submit. Check same cycle/sequence/deadline; no attenuation skips an admitted phase.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; control.submit and the grant must authorize control.submit. Applicable grant purposes include
  ;; control. Depending on the selected inputs and plan, the VM also checks device.submit,
  ;; device.stop, resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the control.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `cycle` (`u64`), `sequence` (`u64`), `controller_epoch` (`u64`), `schema`
  ;;   (`profile`), `command` (`message`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "control.submit" (func $wr_control_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.describe. Actual provider/firmware support, state and watchdog contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; device.describe and the grant must authorize device.describe. Applicable grant purposes include
  ;; device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `device` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `description`
  ;;   (`device_description`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "device.describe" (func $wr_device_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.open. Approved bus/protocol/command envelope, independent watchdog and finite capacity.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.open
  ;; and the grant must authorize device.open. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "device.open" (func $wr_device_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.result. Distinguish accepted, observed execution, partial and unknown effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.result
  ;; and the grant must authorize device.result. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.result action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `device` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `evidence` (`optional<execution_evidence>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.result" (func $wr_device_result (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.stop. Requires explicit stop authority; trusted watchdog independent.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.stop
  ;; and the grant must authorize device.stop. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `device` (`u64`), `profile` (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.stop" (func $wr_device_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.submit. Full command bounds/freshness/units/frame before hardware effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.submit
  ;; and the grant must authorize device.submit. Applicable grant purposes include device. Depending
  ;; on the selected inputs and plan, the VM also checks device.stop, control.submit,
  ;; resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `command`
  ;;   (`command`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.submit" (func $wr_device_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; diagnostic.read. Bounded metadata counters, denial/loss/timeout/provider states; content
  ;; inspection separate.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; diagnostic.read and the grant must authorize diagnostic.read. Applicable grant purposes include
  ;; diagnostic. Depending on the selected inputs and plan, the VM also checks resource.observe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the diagnostic.read action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `source_capability` (`u64`), `cursor` (`optional<u64>`), `limit` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most 40
  ;;   bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`diagnostic_page`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "diagnostic.read" (func $wr_diagnostic_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; event.stream.close. Detach exact stream and wake waiters without closing sources.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; event.stream.close and the grant must authorize event.stream.close. Applicable grant purposes
  ;; include event.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the event.stream.close action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `stream` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `closed` (`bool`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "event.stream.close" (func $wr_event_stream_close (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; event.stream.open. Authorize each observed source and field policy; source references use
  ;; capability/resource pair.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; event.stream.open and the grant must authorize event.stream.open. Applicable grant purposes
  ;; include event. Depending on the selected inputs and plan, the VM also checks resource.observe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the event.stream.open action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `sources`
  ;;   (`array<source_ref>`), `profile` (`profile`), `capacity` (`capacity`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "event.stream.open" (func $wr_event_stream_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; event.stream.poll. Copy complete records before consumption; explicit loss and generation;
  ;; bounded steady deadline.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; event.stream.poll and the grant must authorize event.stream.poll. Applicable grant purposes
  ;; include event. Depending on the selected inputs and plan, the VM also checks resource.observe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the event.stream.poll action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `stream` (`u64`),
  ;;   `limit` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Exact request length, 24 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `events`
  ;;   (`array<event_record>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "event.stream.poll" (func $wr_event_stream_poll (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; graph.snapshot. Exact filtered discovery through an explicitly owned observer node and context;
  ;; observer node profile and actual parent context must match, with counted attachment capacity and
  ;; complete origin authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; graph.snapshot and the grant must authorize graph.snapshot. Applicable grant purposes include
  ;; discovery. Depending on the selected inputs and plan, the VM also checks context.describe,
  ;; node.open, context.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the graph.snapshot action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `context_capability`
  ;;   (`u64`), `context` (`u64`), `observer_node_capability` (`u64`), `observer_node` (`u64`),
  ;;   `profile` (`profile`), `cursor` (`optional<u64>`), `limit` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page` (`page`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "graph.snapshot" (func $wr_graph_snapshot (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; graph.watch. Exact filtered discovery through an explicitly owned observer node and context;
  ;; observer node profile and actual parent context must match, with counted attachment capacity and
  ;; complete origin authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose graph.watch
  ;; and the grant must authorize graph.watch. Applicable grant purposes include discovery. Depending
  ;; on the selected inputs and plan, the VM also checks context.describe, node.open, context.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the graph.watch action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `context_capability`
  ;;   (`u64`), `context` (`u64`), `observer_node_capability` (`u64`), `observer_node` (`u64`),
  ;;   `profile` (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "graph.watch" (func $wr_graph_watch (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; guard.create. Create owned guard, rollback if handle delivery fails.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose guard.create
  ;; and the grant must authorize guard.create. Applicable grant purposes include guard.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the guard.create action in the caller's environment.
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
  (import "uwvm_ros_v2" "guard.create" (func $wr_guard_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; guard.take. Consume pending count only after checked delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose guard.take
  ;; and the grant must authorize guard.take. Applicable grant purposes include guard.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the guard.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `guard` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `count` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "guard.take" (func $wr_guard_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; guard.trigger. Increment guard generation under exact owner grant.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose guard.trigger
  ;; and the grant must authorize guard.trigger. Applicable grant purposes include guard.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the guard.trigger action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `guard` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "guard.trigger" (func $wr_guard_trigger (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; log.emit. Independent log grant, bounded private content and declared attenuation; no
  ;; format-string execution.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose log.emit and
  ;; the grant must authorize log.emit. Applicable grant purposes include log.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the log.emit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `session` (`u64`),
  ;;   `sequence` (`u64`), `severity` (`text`), `logger` (`text`), `stamp` (`optional<log_stamp>`),
  ;;   `message` (`text`), `location` (`optional<log_location>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`log_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "log.emit" (func $wr_log_emit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; media.close. Only owned stream/viewer; no unrelated listener shutdown.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose media.close
  ;; and the grant must authorize media.close. Applicable grant purposes include media.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the media.close action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `stream` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "media.close" (func $wr_media_close (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; media.open. Separate codec/ingress/egress/viewer and listener profile grants.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose media.open
  ;; and the grant must authorize media.open. Applicable grant purposes include media. Depending on
  ;; the selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create,
  ;; buffer.write, buffer.seal.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the media.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`), `source` (`resource_ref`), `output_capability` (`u64`), `egress`
  ;;   (`optional<resource_ref>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "media.open" (func $wr_media_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; media.submit. Bound decoded expansion, encoded output and egress destination.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose media.submit
  ;; and the grant must authorize media.submit. Applicable grant purposes include media. Depending on
  ;; the selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create,
  ;; buffer.write, buffer.seal.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the media.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `stream` (`u64`), `frame` (`buffer_ref`), `description` (`media_frame`),
  ;;   `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "media.submit" (func $wr_media_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; media.take. Complete bounded encoded/decoded frame under profile.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose media.take
  ;; and the grant must authorize media.take. Applicable grant purposes include media. Depending on
  ;; the selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create,
  ;; buffer.write, buffer.seal.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the media.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `stream` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `record`
  ;;   (`media_delivery`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "media.take" (func $wr_media_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; model.cancel. Cancel request acknowledgement distinct from actual provider termination.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose model.cancel
  ;; and the grant must authorize model.cancel. Applicable grant purposes include model.language,
  ;; model.vision, model.world.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the model.cancel action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `session` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "model.cancel" (func $wr_model_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; model.describe. Actual schema/placement support; no credentials/prompts/payload.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; model.describe and the grant must authorize model.describe. Applicable grant purposes include
  ;; model.language, model.vision, model.world.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the model.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `session` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `profile`
  ;;   (`profile`), `supported` (`array<text>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "model.describe" (func $wr_model_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; model.open. Exact model/provider/task identities and reserved session capacity.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose model.open
  ;; and the grant must authorize model.open. Applicable grant purposes include model.language,
  ;; model.vision, model.world.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the model.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4206592 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "model.open" (func $wr_model_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; model.submit. Pin immutable inputs, data-egress grants and full task limits before work.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose model.submit
  ;; and the grant must authorize model.submit. Applicable grant purposes include model.language,
  ;; model.vision, model.world. Depending on the selected inputs and plan, the VM also checks
  ;; buffer.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the model.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `inference`
  ;;   (`inference`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4206592 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "model.submit" (func $wr_model_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; model.take. Streaming/terminal output explicitly distinguished; nonconsuming failed copy.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose model.take
  ;; and the grant must authorize model.take. Applicable grant purposes include model.language,
  ;; model.vision, model.world.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the model.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `session` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `output` (`optional<delivery>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "model.take" (func $wr_model_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.acknowledge. Require delivered result and empty payload. Overwrite every retained
  ;; region and host capacity before reusing slot. Exact retry with unchanged retained token carries
  ;; no new data. Cleanup bypasses traffic quotas but requires authority. Trusted startup route fixes
  ;; exact endpoint names, semantic operation, opaque schema identities, finite
  ;; byte/slot/reservation/deadline ceilings. No arbitrary export invocation. Inputs and registered
  ;; delivery regions must use owned, unexported shared memory; imported memory, exported memory,
  ;; nonshared heaps, active threaded host calls and resumable/replay compilation profiles are
  ;; refused. A live debugger value-observation profile is allowed; it does not grant recording,
  ;; restoration or message authority. Detached scene queries never copy payloads; separately
  ;; authorized debugger memory reads remain subject to debugger disclosure policy. Input carrier is
  ;; copied with byte atomics and zeroed before dispatch by default. Trusted startup bool
  ;; clear_after_copy defaults to true; false retains sender input bytes, including failure cleanup,
  ;; without weakening authorization, bounds, tags or broker/delivery erasure. Guest requests cannot
  ;; change this frozen per-route policy. Retained spans cannot overlap across outstanding
  ;; calls/routes. Full buffer capacity is overwritten on consume, response, acknowledge, cancel,
  ;; observed expiry, revoke and retirement. Failed erasure quarantines the slot. Expiry is lazy, not
  ;; a hard timer; independent guest copies are outside this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.acknowledge and the grant must authorize module.call.acknowledge. Applicable grant
  ;; purposes include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.acknowledge action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) Exactly 16 bytes for the token and zero payload length.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. Zero
  ;;   capacity is allowed for this empty reply.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero writes zero to the length slot after releasing the registered delivery. The same
  ;;   token can be acknowledged again while its freed slot still carries that token. UNSUPPORTED
  ;;   (95) can indicate failure to capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.acknowledge" (func $wr_module_call_acknowledge (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.cancel. Either registered endpoint may cancel its exact token with empty payload.
  ;; Overwrite both delivery regions and host capacity. No foreign policy mutation; cleanup bypasses
  ;; traffic quotas but requires authority. Trusted startup route fixes exact endpoint names,
  ;; semantic operation, opaque schema identities, finite byte/slot/reservation/deadline ceilings. No
  ;; arbitrary export invocation. Inputs and registered delivery regions must use owned, unexported
  ;; shared memory; imported memory, exported memory, nonshared heaps, active threaded host calls and
  ;; resumable/replay compilation profiles are refused. A live debugger value-observation profile is
  ;; allowed; it does not grant recording, restoration or message authority. Detached scene queries
  ;; never copy payloads; separately authorized debugger memory reads remain subject to debugger
  ;; disclosure policy. Input carrier is copied with byte atomics and zeroed before dispatch by
  ;; default. Trusted startup bool clear_after_copy defaults to true; false retains sender input
  ;; bytes, including failure cleanup, without weakening authorization, bounds, tags or
  ;; broker/delivery erasure. Guest requests cannot change this frozen per-route policy. Retained
  ;; spans cannot overlap across outstanding calls/routes. Full buffer capacity is overwritten on
  ;; consume, response, acknowledge, cancel, observed expiry, revoke and retirement. Failed erasure
  ;; quarantines the slot. Expiry is lazy, not a hard timer; independent guest copies are outside
  ;; this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.cancel and the grant must authorize module.call.cancel. Applicable grant purposes
  ;; include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.cancel action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) Exactly 16 bytes for the token and zero payload length.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. Zero
  ;;   capacity is allowed for this empty reply.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero writes zero to the length slot after erasing the exchange for this token. Failed
  ;;   erasure returns IO (5) and quarantines the slot. UNSUPPORTED (95) can indicate failure to
  ;;   capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.cancel" (func $wr_module_call_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.respond. Require received request token and exact server incarnation. Copy bounded
  ;; response and overwrite server delivery region before committing responded state. Lost output
  ;; does not resend or discard the committed response. Trusted startup route fixes exact endpoint
  ;; names, semantic operation, opaque schema identities, finite byte/slot/reservation/deadline
  ;; ceilings. No arbitrary export invocation. Inputs and registered delivery regions must use owned,
  ;; unexported shared memory; imported memory, exported memory, nonshared heaps, active threaded
  ;; host calls and resumable/replay compilation profiles are refused. A live debugger
  ;; value-observation profile is allowed; it does not grant recording, restoration or message
  ;; authority. Detached scene queries never copy payloads; separately authorized debugger memory
  ;; reads remain subject to debugger disclosure policy. Input carrier is copied with byte atomics
  ;; and zeroed before dispatch by default. Trusted startup bool clear_after_copy defaults to true;
  ;; false retains sender input bytes, including failure cleanup, without weakening authorization,
  ;; bounds, tags or broker/delivery erasure. Guest requests cannot change this frozen per-route
  ;; policy. Retained spans cannot overlap across outstanding calls/routes. Full buffer capacity is
  ;; overwritten on consume, response, acknowledge, cancel, observed expiry, revoke and retirement.
  ;; Failed erasure quarantines the slot. Expiry is lazy, not a hard timer; independent guest copies
  ;; are outside this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.respond and the grant must authorize module.call.respond. Applicable grant purposes
  ;; include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.respond action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) 16 bytes of token and payload length plus payload bytes, at most 4194320
  ;;   bytes. The route also bounds the payload.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. At
  ;;   least 16 bytes are required for the frame header.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero delivers a 16-byte receipt with the request token and an empty payload. Exceeding
  ;;   the route's response limit returns TOO_LARGE (90) without a required length. A failed receipt
  ;;   copy after commit leaves the response available to the client. UNSUPPORTED (95) can indicate
  ;;   failure to capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.respond" (func $wr_module_call_respond (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.result. Require exact original client token and empty payload. Copy committed
  ;; response once and retain client erasure region until acknowledge. Pending returns again;
  ;; duplicate consumption conflicts. Trusted startup route fixes exact endpoint names, semantic
  ;; operation, opaque schema identities, finite byte/slot/reservation/deadline ceilings. No
  ;; arbitrary export invocation. Inputs and registered delivery regions must use owned, unexported
  ;; shared memory; imported memory, exported memory, nonshared heaps, active threaded host calls and
  ;; resumable/replay compilation profiles are refused. A live debugger value-observation profile is
  ;; allowed; it does not grant recording, restoration or message authority. Detached scene queries
  ;; never copy payloads; separately authorized debugger memory reads remain subject to debugger
  ;; disclosure policy. Input carrier is copied with byte atomics and zeroed before dispatch by
  ;; default. Trusted startup bool clear_after_copy defaults to true; false retains sender input
  ;; bytes, including failure cleanup, without weakening authorization, bounds, tags or
  ;; broker/delivery erasure. Guest requests cannot change this frozen per-route policy. Retained
  ;; spans cannot overlap across outstanding calls/routes. Full buffer capacity is overwritten on
  ;; consume, response, acknowledge, cancel, observed expiry, revoke and retirement. Failed erasure
  ;; quarantines the slot. Expiry is lazy, not a hard timer; independent guest copies are outside
  ;; this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.result and the grant must authorize module.call.result. Applicable grant purposes
  ;; include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage. On successful delivery reserve the full
  ;; reply capacity and length slot until the client acknowledges or confirmed cleanup erases the
  ;; registered region. Cancellation, observed expiry, revocation and retirement can erase it.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.result action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) Exactly 16 bytes for the token and zero payload length.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. At
  ;;   least 16 bytes are required for the frame header.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero delivers the token and committed response. A pending response returns AGAIN (11).
  ;;   If the frame exceeds capacity, TOO_LARGE (90) preserves the response and supplies no required
  ;;   length. Repeating a completed delivery returns CONFLICT (17). UNSUPPORTED (95) can indicate
  ;;   failure to capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.result" (func $wr_module_call_result (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.submit. Require registered server incarnation, fixed caller role and token=0.
  ;; Reserve a free slot, copy bounded request, return nonzero token. Failed delivery discards the
  ;; unpublished request. Trusted startup route fixes exact endpoint names, semantic operation,
  ;; opaque schema identities, finite byte/slot/reservation/deadline ceilings. No arbitrary export
  ;; invocation. Inputs and registered delivery regions must use owned, unexported shared memory;
  ;; imported memory, exported memory, nonshared heaps, active threaded host calls and
  ;; resumable/replay compilation profiles are refused. A live debugger value-observation profile is
  ;; allowed; it does not grant recording, restoration or message authority. Detached scene queries
  ;; never copy payloads; separately authorized debugger memory reads remain subject to debugger
  ;; disclosure policy. Input carrier is copied with byte atomics and zeroed before dispatch by
  ;; default. Trusted startup bool clear_after_copy defaults to true; false retains sender input
  ;; bytes, including failure cleanup, without weakening authorization, bounds, tags or
  ;; broker/delivery erasure. Guest requests cannot change this frozen per-route policy. Retained
  ;; spans cannot overlap across outstanding calls/routes. Full buffer capacity is overwritten on
  ;; consume, response, acknowledge, cancel, observed expiry, revoke and retirement. Failed erasure
  ;; quarantines the slot. Expiry is lazy, not a hard timer; independent guest copies are outside
  ;; this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.submit and the grant must authorize module.call.submit. Applicable grant purposes
  ;; include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.submit action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) 16 bytes of token and payload length plus payload bytes, at most 4194320
  ;;   bytes. The route also bounds the payload.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. At
  ;;   least 16 bytes are required for the frame header.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero delivers a 16-byte receipt with a new nonzero token and an empty payload. AGAIN
  ;;   (11) can mean the server has not registered or the route has no free slot. UNSUPPORTED (95)
  ;;   can indicate failure to capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.submit" (func $wr_module_call_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.call.take. Require exact server role, token=0 and empty payload. First authorized take
  ;; pins server incarnation even when returning again. Copy queued request once into a registered
  ;; erasure region; preserve request on failed delivery. Trusted startup route fixes exact endpoint
  ;; names, semantic operation, opaque schema identities, finite byte/slot/reservation/deadline
  ;; ceilings. No arbitrary export invocation. Inputs and registered delivery regions must use owned,
  ;; unexported shared memory; imported memory, exported memory, nonshared heaps, active threaded
  ;; host calls and resumable/replay compilation profiles are refused. A live debugger
  ;; value-observation profile is allowed; it does not grant recording, restoration or message
  ;; authority. Detached scene queries never copy payloads; separately authorized debugger memory
  ;; reads remain subject to debugger disclosure policy. Input carrier is copied with byte atomics
  ;; and zeroed before dispatch by default. Trusted startup bool clear_after_copy defaults to true;
  ;; false retains sender input bytes, including failure cleanup, without weakening authorization,
  ;; bounds, tags or broker/delivery erasure. Guest requests cannot change this frozen per-route
  ;; policy. Retained spans cannot overlap across outstanding calls/routes. Full buffer capacity is
  ;; overwritten on consume, response, acknowledge, cancel, observed expiry, revoke and retirement.
  ;; Failed erasure quarantines the slot. Expiry is lazy, not a hard timer; independent guest copies
  ;; are outside this erasure contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; module.call.take and the grant must authorize module.call.take. Applicable grant purposes
  ;; include module.call.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap. Use caller-defined shared memory in a module with no
  ;; memory exports. Give the VM writable access to the entire input when the route erases it after
  ;; copying (the default). A span that intersects an outstanding delivery returns CONFLICT (17).
  ;; Coordinate concurrent access to all exchange storage. On successful delivery reserve the full
  ;; reply capacity and length slot until the server responds or confirmed cleanup erases the
  ;; registered region. Cancellation, observed expiry, revocation and retirement can erase it.
  ;;
  ;; @param $cap - (i64) Capability handle for the module.call.take action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's owned shared exchange memory.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`). The frame starts with the little-endian u64 token and payload byte count.
  ;; @param $size - (i64) Exactly 16 bytes for the token and zero payload length.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `token` (`u64`),
  ;;   `payload` (`bytes`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194320. At
  ;;   least 16 bytes are required for the frame header.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. This carrier does not publish a
  ;;   required size on TOO_LARGE (90).
  ;; @returns Zero delivers the token and queued request. An empty queue returns AGAIN (11). If the
  ;;   frame exceeds capacity, TOO_LARGE (90) leaves the request queued and supplies no required
  ;;   length. UNSUPPORTED (95) can indicate failure to capture an eligible tagged exchange span.
  (import "uwvm_ros_v2" "module.call.take" (func $wr_module_call_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.describe. Return the exact registered target name and kind: main-wasm, preload-wasm or
  ;; preload-dl. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.describe. The request alias must select a
  ;; module/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output.
  (import "uwvm_ros_v2" "module.describe" (func $wr_module_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.exports. Return only export names already recorded in the module registry. Do not resolve
  ;; or call a symbol. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.exports. The request alias must select a
  ;; module/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output.
  (import "uwvm_ros_v2" "module.exports" (func $wr_module_exports (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.group. Return the target ROSv2 group name and its members only under this independent
  ;; action. Default authority is zero: require explicit import exposure and exact module/metadata
  ;; grant action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
  ;; wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
  ;; runtime. Observation never freezes deployment, enrolls a caller, opens a capability, replenishes
  ;; or consumes execution quotas, starts a provider, invokes an export, reads foreign memory, or
  ;; changes another policy. A denial writes neither result nor length. Owned temporary buffers are
  ;; securely overwritten.
  ;;
  ;; The caller's deployment must expose module.group. The request alias must select a
  ;; module/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output. A target without a ROSv2 group yields a supported page with enabled=false.
  (import "uwvm_ros_v2" "module.group" (func $wr_module_group (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.importers. Return direct registered Wasm importers of the exact target, as importer
  ;; module/symbol rows. Require an independent module/metadata grant and exact exposure even when
  ;; the target is the caller. Count all visited modules and imports, including nonmatches, against
  ;; the finite scan budget. Reexports are not expanded and native dynamic-linker dependencies are
  ;; not inspected. An explicit grant may also name a registered builtin module. No unrelated peers
  ;; or their remaining imports are disclosed. Carrier capability must be zero. Exact immediate
  ;; caller identity comes from the runtime. Observation never freezes deployment, enrolls a caller,
  ;; opens a capability, replenishes or consumes execution quotas, starts a provider, invokes an
  ;; export, reads foreign memory, or changes another policy. A denial writes neither result nor
  ;; length. Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.importers. The request alias must select a
  ;; module/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output. The scan budget counts all visited modules and import declarations, including
  ;;   nonmatches.
  (import "uwvm_ros_v2" "module.importers" (func $wr_module_importers (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.imports. Return the exact Wasm import module/name pairs; native preloaddl platform
  ;; imports are unsupported. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.imports. The request alias must select a
  ;; module/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output. Native modules have no registered Wasm import list.
  (import "uwvm_ros_v2" "module.imports" (func $wr_module_imports (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.permission.report. Return permissions of the exact registered target for the requested
  ;; family. The viewer observation policy also applies, including exact-function and aggregate
  ;; denials. Default authority is zero: require explicit import exposure and exact module/metadata
  ;; grant action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
  ;; wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
  ;; runtime. Observation never freezes deployment, enrolls a caller, opens a capability, replenishes
  ;; or consumes execution quotas, starts a provider, invokes an export, reads foreign memory, or
  ;; changes another policy. A denial writes neither result nor length. Owned temporary buffers are
  ;; securely overwritten.
  ;;
  ;; The caller's deployment must expose module.permission.report. The request alias must select a
  ;; module/metadata grant with this exact action. The viewer's family and exact-function observation
  ;; restrictions also apply.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `family` (`text`), `function` (`text`), `first` (`u64`). The cursor first is a
  ;;   zero-based row index, at most 65536. Select preloaddl, preloadwasm, wasip1, ros1v1, ros2v1 or
  ;;   rosv2. An empty function selects the whole family.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   558 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. Initialize this slot to zero to
  ;;   distinguish a delivered status-95 page from a refusal that writes nothing.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. For an authorized whole-family query with a valid cursor, an unbuilt family
  ;;   returns UNSUPPORTED (95) with a supported=false, enabled=false page when it fits. An
  ;;   unsupported exact-function query returns 95 without writing the page or length. A built but
  ;;   disabled family can return zero with enabled=false. An unsupported target identity can also
  ;;   return 95 before either output is written.
  (import "uwvm_ros_v2" "module.permission.report" (func $wr_module_permission_report (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; node.describe. Only owned resolved identity and enabled features.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose node.describe
  ;; and the grant must authorize node.describe. Applicable grant purposes include node.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the node.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `node` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `name` (`text`),
  ;;   `namespace` (`text`), `profile` (`profile`), `generation` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "node.describe" (func $wr_node_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; node.open. Resolve immutable node/name/remapping/profile under exact parent context grant.
  ;; Creation is asynchronous: explicit monotonically increasing key and finite absolute steady
  ;; deadline; response is a request receipt, not an endpoint. communication.open.take retrieves a
  ;; separately published typed handle.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose node.open and
  ;; the grant must authorize node.open. Applicable grant purposes include node. Depending on the
  ;; selected inputs and plan, the VM also checks context.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the node.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `context_capability`
  ;;   (`u64`), `context` (`u64`), `profile` (`profile`), `creation_key` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "node.open" (func $wr_node_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.declare. Declaration respects override/dynamic/read-only policy without ambient YAML
  ;; access.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.declare and the grant must authorize parameter.declare. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.declare action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `scope` (`u64`), `descriptor` (`parameter_descriptor`), `initial`
  ;;   (`parameter_value`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "parameter.declare" (func $wr_parameter_declare (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.describe. Only granted descriptor metadata.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.describe and the grant must authorize parameter.describe. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `names` (`array<text>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `descriptors`
  ;;   (`array<parameter_descriptor>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.describe" (func $wr_parameter_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.exists. Authorize the exact resolved key before existence lookup. Read-only existence
  ;; authority reveals neither value nor descriptor and is independent of get/list. Missing,
  ;; uninitialized and denied are distinct; denied never returns false as if absent.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.exists and the grant must authorize parameter.exists. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.exists action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `name` (`text`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `exists` (`bool`),
  ;;   `initialized` (`bool`), `snapshot_revision` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 24 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.exists" (func $wr_parameter_exists (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.get. Bounded batch; missing/uninitialized/denied are not silently conflated.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose parameter.get
  ;; and the grant must authorize parameter.get. Applicable grant purposes include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.get action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `names` (`array<text>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `values`
  ;;   (`array<parameter_item>`), `revision` (`optional<u64>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.get" (func $wr_parameter_get (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.list. Bounded filtered key listing; counts and cursors obey same visibility. Name
  ;; entries use fixed message type_identity ros.parameter.name and encoding canonical.text; each
  ;; body is exactly one canonical wire text.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.list and the grant must authorize parameter.list. Applicable grant purposes include
  ;; parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.list action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `prefixes` (`array<text>`), `depth` (`u64`), `cursor` (`optional<u64>`), `limit` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page` (`page`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.list" (func $wr_parameter_list (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.open. Bind exact parameter keys, value algebra, descriptors and role.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.open and the grant must authorize parameter.open. Applicable grant purposes include
  ;; parameter. Depending on the selected inputs and plan, the VM also checks node.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `node_capability`
  ;;   (`u64`), `node` (`u64`), `profile` (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.open" (func $wr_parameter_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.respond. Current validator generation/deadline; transformed keys and values
  ;; revalidated; no recursive mutation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.respond and the grant must authorize parameter.respond. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.respond action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `request` (`u64`), `accepted` (`bool`), `replacement` (`optional<array<parameter_item>>`),
  ;;   `reason` (`text`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "parameter.respond" (func $wr_parameter_respond (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.search. ROS1 ancestor search within a deployment-fixed canonical namespace root and
  ;; finite candidate-count bound, including the starting namespace. Authorize each exact candidate
  ;; key before existence lookup; return denied at the first unauthorized candidate. Exhaustion
  ;; returns too_large; only reaching the root with no match returns not-found. One coherent local
  ;; store snapshot supplies a revision even for negative results. No ambient namespace, filesystem
  ;; path or unrestricted discovery. This local provider does not impersonate a native parameter
  ;; server.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.search and the grant must authorize parameter.search. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.search action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`),
  ;;   `name` (`text`), `start_namespace` (`text`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `resolved_name`
  ;;   (`optional<text>`), `snapshot_revision` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.search" (func $wr_parameter_search (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.set. Per-item writes; report every committed/rejected/unknown decision.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose parameter.set
  ;; and the grant must authorize parameter.set. Applicable grant purposes include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.set action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `transaction`
  ;;   (`parameter_transaction`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `decisions` (`array<parameter_decision>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "parameter.set" (func $wr_parameter_set (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.set.atomic. All or none only within qualified provider atomic domain; do not fake
  ;; cross-node CAS. A ROS1 provider must separately declare atomic upsert of permitted undeclared
  ;; keys and subtree replacement semantics; ROS2 declaration rules remain distinct. Native bridging
  ;; cannot silently emulate atomic upsert with a racy get/declare/set sequence.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.set.atomic and the grant must authorize parameter.set.atomic. Applicable grant
  ;; purposes include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.set.atomic action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `transaction`
  ;;   (`parameter_transaction`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `accepted` (`bool`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "parameter.set.atomic" (func $wr_parameter_set_atomic (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.take. Deliver validation or committed event; no native callback into guest.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.take and the grant must authorize parameter.take. Applicable grant purposes include
  ;; parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `scope` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `event`
  ;;   (`parameter_event`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "parameter.take" (func $wr_parameter_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; parameter.undeclare. Explicit deletion distinct from not-set/uninitialized value.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; parameter.undeclare and the grant must authorize parameter.undeclare. Applicable grant purposes
  ;; include parameter.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the parameter.undeclare action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `scope` (`u64`), `name` (`text`), `expected_revision` (`optional<u64>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "parameter.undeclare" (func $wr_parameter_undeclare (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; permission.report. Self observation defaults to allowed only after explicit ROSv2 binding.
  ;; Family and exact function denials can only reduce observation; any exact denial refuses the full
  ;; aggregate to prevent bypass. Explicit hidden removes the import. Returns own identity, exact
  ;; import exposure, configured/live ROSv2 permissions and own group name without other members.
  ;; WASI descriptor rows are initial approved rights; ROSv1 rows are configured policy, not a
  ;; complete live handle snapshot. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The VM authenticates the immediate caller and applies that caller's ROSv2 membership, import
  ;; exposure and observation policy.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `family` (`text`),
  ;;   `function` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
  ;;   65536. Select preloaddl, preloadwasm, wasip1, ros1v1, ros2v1 or rosv2. An empty function
  ;;   selects the whole family.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   295 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. Initialize this slot to zero to
  ;;   distinguish a delivered status-95 page from a refusal that writes nothing.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. For an authorized whole-family query with a valid cursor, an unbuilt family
  ;;   returns UNSUPPORTED (95) with a supported=false, enabled=false page when it fits. An
  ;;   unsupported exact-function query returns 95 without writing the page or length. A built but
  ;;   disabled family can return zero with enabled=false.
  (import "uwvm_ros_v2" "permission.report" (func $wr_permission_report (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.accept. Independent arbiter and exact current target action/argument constraints;
  ;; cannot broaden rights.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.accept and the grant must authorize proposal.accept. Applicable grant purposes include
  ;; arbiter. Depending on the selected inputs and plan, the VM also checks proposal.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.accept action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `proposal_capability` (`u64`), `proposal` (`u64`), `target_capability`
  ;;   (`u64`), `target` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "proposal.accept" (func $wr_proposal_accept (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.capture. Explicit finite capture of actual typed source observations and ordered sealed
  ;; buffers; exact per-capability key replay. Closing capture releases only its own pins. No model
  ;; execution or target effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.capture and the grant must authorize proposal.capture. Applicable grant purposes
  ;; include proposal. Depending on the selected inputs and plan, the VM also checks
  ;; resource.observe, buffer.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.capture action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `profile` (`profile`), `sources` (`array<proposal_capture_source>`), `expiry`
  ;;   (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `capture` (`u64`),
  ;;   `inputs` (`array<proposal_captured_buffer>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.capture" (func $wr_proposal_capture (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.publish. Authenticate complete successful terminal output from the actual model request
  ;; against original captured input IDs, SHA and order. Independently authorize publication; model
  ;; bytes cannot issue grants or execute tools.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.publish and the grant must authorize proposal.publish. Applicable grant purposes
  ;; include proposal. Depending on the selected inputs and plan, the VM also checks model.take.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.publish action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `capture` (`u64`), `model_request` (`u64`), `envelope` (`bytes`), `expiry`
  ;;   (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `proposal` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.publish" (func $wr_proposal_publish (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.read. Read inert validated model proposal and trusted provenance.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose proposal.read
  ;; and the grant must authorize proposal.read. Applicable grant purposes include proposal.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `proposal` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `proposal`
  ;;   (`proposal`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.read" (func $wr_proposal_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; qos.acknowledgements.wait. Wait for defined native acknowledgement horizon; unsupported is not
  ;; success.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; qos.acknowledgements.wait and the grant must authorize qos.acknowledgements.wait. Applicable
  ;; grant purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the qos.acknowledgements.wait action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`),
  ;;   `deadline` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "qos.acknowledgements.wait" (func $wr_qos_acknowledgements_wait (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; qos.describe. Requested/effective/supported settings; unavailable values remain absent.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose qos.describe
  ;; and the grant must authorize qos.describe. Applicable grant purposes include topic, service,
  ;; action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the qos.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `qos` (`qos_info`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "qos.describe" (func $wr_qos_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; qos.liveliness.assert. Only publisher role and qualified native manual-liveliness support.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; qos.liveliness.assert and the grant must authorize qos.liveliness.assert. Applicable grant
  ;; purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the qos.liveliness.assert action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `endpoint` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "qos.liveliness.assert" (func $wr_qos_liveliness_assert (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; request.describe. No extra native effect; requires origin grant and request ownership.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; request.describe and the grant must authorize request.describe. The request's originating grant
  ;; and provider binding select the ledger.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the request.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "request.describe" (func $wr_request_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; request.release. Only terminal receipt retirement; unresolved effect/cleanup debt not forgiven.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; request.release and the grant must authorize request.release. The request's originating grant
  ;; and provider binding select the ledger.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the request.release action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `released` (`bool`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194816. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "request.release" (func $wr_request_release (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; resource.close. Close an owned local scheduling, lifecycle, sealed-buffer, model or transform
  ;; resource according to its cleanup contract. Retained borrows or cleanup debt retain their
  ;; capacity until actual retirement; closure does not grant another purpose. Sensor/proposal and
  ;; recording/replay handles route to their owning dispatchers; retained borrows/pins still prevent
  ;; premature retirement.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; resource.close and the grant must authorize resource.close. The resource registry checks the
  ;; originating grant and provider binding.
  ;;
  ;; Encode and decode scalar words as little-endian u64. Signed values use their two's-complement
  ;; bit pattern.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the resource.close action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `resource` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the checked reply range. This operation has an empty
  ;;   reply body.
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 0 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. The VM writes a zero length before the
  ;;   mutation. A later refusal can therefore also leave zero in the slot.
  (import "uwvm_ros_v2" "resource.close" (func $wr_resource_close (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; sensor.describe. Bound source identity, loss and negotiated capabilities; no credentials.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; sensor.describe and the grant must authorize sensor.describe. Applicable grant purposes include
  ;; sensor.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the sensor.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `sensor` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `profile`
  ;;   (`profile`), `state` (`message`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4196352.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "sensor.describe" (func $wr_sensor_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; sensor.open. Ingress-only approved source/transport/schema/queue; no send/listen authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose sensor.open
  ;; and the grant must authorize sensor.open. Applicable grant purposes include sensor.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the sensor.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   144 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4196352. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "sensor.open" (func $wr_sensor_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; sensor.take. Validated complete frame with timestamp origin and discontinuity. Capacity for the
  ;; largest complete frame is checked before native read. The local capture ordinal and optional
  ;; actual native sequence are distinct. Failed guest copy retains the frame for retry.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose sensor.take
  ;; and the grant must authorize sensor.take. Applicable grant purposes include sensor. Depending on
  ;; the selected inputs and plan, the VM also checks data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the sensor.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `sensor` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `record`
  ;;   (`delivery`), `buffer` (`u64`), `schema` (`profile`), `buffer_profile` (`profile`), `frame`
  ;;   (`text`), `units` (`text`), `source` (`u64`), `native_sequence` (`optional<u64>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4196352.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "sensor.take" (func $wr_sensor_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.abandon. Retire local wait/response interest; never claim remote cancellation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.abandon and the grant must authorize service.abandon. Applicable grant purposes include
  ;; service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.abandon action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `client` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.abandon" (func $wr_service_abandon (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.acknowledge. Consume exactly the previously reserved record after guest processing.
  ;; Exact replay is idempotent; stale generation, wrong consumer, altered nonce or expired
  ;; reservation is refused. Lost native ACK is outcome_unknown and never triggers blind
  ;; re-consumption. Bounded receipt survives failed guest delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.acknowledge and the grant must authorize service.acknowledge. Applicable grant purposes
  ;; include service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.acknowledge action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `reservation` (`reservation_ref`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.acknowledge" (func $wr_service_acknowledge (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.available. Observe native readiness on the exact live client. Direct client grants
  ;; supply source_capability zero. A service-observer grant requires its separately authorized
  ;; registered source service.submit capability. Only the observer is charged. Either authorization
  ;; may prevent result delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.available and the grant must authorize service.available. Applicable grant purposes
  ;; include service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.available action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `client` (`u64`),
  ;;   `source_capability` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `available` (`bool`),
  ;;   `observed` (`stamp`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 32 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "service.available" (func $wr_service_available (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.describe. Inspect the exact retained native client/server endpoint and each
  ;; request/response QoS leg. Support/absence is explicit; profile configuration never stands in for
  ;; actual getter evidence. Observation grants no submission, response, borrow or discovery
  ;; authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.describe and the grant must authorize service.describe. Applicable grant purposes
  ;; include service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `endpoint`
  ;;   (`endpoint_info`), `channels` (`array<endpoint_qos_profile>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "service.describe" (func $wr_service_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.open. Fix client/server role and finite request/response capacities. Creation is
  ;; asynchronous: explicit monotonically increasing key and finite absolute steady deadline;
  ;; response is a request receipt, not an endpoint. communication.open.take retrieves a separately
  ;; published typed handle.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose service.open
  ;; and the grant must authorize service.open. Applicable grant purposes include service. Depending
  ;; on the selected inputs and plan, the VM also checks node.open, type.describe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint`
  ;;   (`endpoint_request`), `creation_key` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.open" (func $wr_service_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.release. Cancel exactly the owned borrow while retaining the original record. This is
  ;; not service-request cancellation or endpoint close. Cleanup uses pre-reserved capacity and is
  ;; not throttled by creation/traffic quotas; uncertain native cancellation retains debt until
  ;; trusted reconciliation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.release and the grant must authorize service.release. Applicable grant purposes include
  ;; service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.release action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `reservation` (`reservation_ref`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.release" (func $wr_service_release (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.reserve. Explicit two-phase receive: independently authorize the exact consumer
  ;; endpoint, retain the original native record and deliver a bounded detached copy without
  ;; acknowledgement. Same-consumer retry returns the retained record/nonce; concurrent consumers
  ;; cannot steal it. Both node/context/schema origins and native metadata remain attached.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.reserve and the grant must authorize service.reserve. Applicable grant purposes include
  ;; service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.reserve action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`),
  ;;   `deadline` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `reservation`
  ;;   (`delivery_reservation`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. The reservation remains owned until acknowledgement or release.
  (import "uwvm_ros_v2" "service.reserve" (func $wr_service_reserve (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.respond. Respond once to an exact live owned received request.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.respond and the grant must authorize service.respond. Applicable grant purposes include
  ;; service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.respond action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `server` (`u64`), `request` (`u64`), `body` (`message`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.respond" (func $wr_service_respond (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.submit. Owned native-correlated request; remote outcome can remain unknown after
  ;; timeout.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; service.submit and the grant must authorize service.submit. Applicable grant purposes include
  ;; service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `client` (`u64`), `body` (`message`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "service.submit" (func $wr_service_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; service.take. Role-specific request/response atomically delivered with correlation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose service.take
  ;; and the grant must authorize service.take. Applicable grant purposes include service.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the service.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `record`
  ;;   (`delivery`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "service.take" (func $wr_service_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  ;; topic.acknowledge. Consume exactly the previously reserved record after guest processing. Exact
  ;; replay is idempotent; stale generation, wrong consumer, altered nonce or expired reservation is
  ;; refused. Lost native ACK is outcome_unknown and never triggers blind re-consumption. Bounded
  ;; receipt survives failed guest delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; topic.acknowledge and the grant must authorize topic.acknowledge. Applicable grant purposes
  ;; include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.acknowledge action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `reservation` (`reservation_ref`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "topic.acknowledge" (func $wr_topic_acknowledge (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.describe. Owned node, resolved endpoint/type/direction and profile, with optional cached
  ;; actual provider incarnation and native identity. Metadata is copied from the same retained
  ;; endpoint; no middleware call or discovery occurs during description. Unknown provider generation
  ;; and GID remain absent. This grants no publication or subscription authority.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; topic.describe and the grant must authorize topic.describe. Applicable grant purposes include
  ;; topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `endpoint`
  ;;   (`endpoint_info`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "topic.describe" (func $wr_topic_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.open. Create exactly one publisher or subscription role. Creation is asynchronous:
  ;; explicit monotonically increasing key and finite absolute steady deadline; response is a request
  ;; receipt, not an endpoint. communication.open.take retrieves a separately published typed handle.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose topic.open
  ;; and the grant must authorize topic.open. Applicable grant purposes include topic. Depending on
  ;; the selected inputs and plan, the VM also checks node.open, type.describe.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint`
  ;;   (`endpoint_request`), `creation_key` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "topic.open" (func $wr_topic_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.publish. Reserve and validate complete message before acceptance; acceptance is not remote
  ;; delivery.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose topic.publish
  ;; and the grant must authorize topic.publish. Applicable grant purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.publish action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `endpoint` (`u64`), `body` (`message`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "topic.publish" (func $wr_topic_publish (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.release. Cancel exactly the owned borrow while retaining the original record. This is not
  ;; service-request cancellation or endpoint close. Cleanup uses pre-reserved capacity and is not
  ;; throttled by creation/traffic quotas; uncertain native cancellation retains debt until trusted
  ;; reconciliation.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose topic.release
  ;; and the grant must authorize topic.release. Applicable grant purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.release action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `reservation` (`reservation_ref`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "topic.release" (func $wr_topic_release (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.reserve. Explicit two-phase receive: independently authorize the exact consumer endpoint,
  ;; retain the original native record and deliver a bounded detached copy without acknowledgement.
  ;; Same-consumer retry returns the retained record/nonce; concurrent consumers cannot steal it.
  ;; Both node/context/schema origins and native metadata remain attached.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose topic.reserve
  ;; and the grant must authorize topic.reserve. Applicable grant purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.reserve action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`),
  ;;   `deadline` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `reservation`
  ;;   (`delivery_reservation`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. The reservation remains owned until acknowledgement or release.
  (import "uwvm_ros_v2" "topic.reserve" (func $wr_topic_reserve (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; topic.take. Receive one source record without consuming on invalid/short output.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose topic.take
  ;; and the grant must authorize topic.take. Applicable grant purposes include topic.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the topic.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `endpoint` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `record`
  ;;   (`delivery`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "topic.take" (func $wr_topic_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.available. Same visibility boundary as lookup; no hidden frame existence leak.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.available and the grant must authorize transform.available. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.available action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `query` (`transform_query`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `available` (`bool`),
  ;;   `reason` (`text`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "transform.available" (func $wr_transform_available (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.cancel. Cancel owned query and wake waiters.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.cancel and the grant must authorize transform.cancel. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.cancel action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "transform.cancel" (func $wr_transform_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.clear. Explicit history mutation and pending query invalidation; static policy
  ;; separate.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.clear and the grant must authorize transform.clear. Applicable grant purposes include
  ;; transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.clear action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `buffer` (`u64`), `expected_generation` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "transform.clear" (func $wr_transform_clear (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.lookup. Enforce all query-path frames, epochs and cache bounds.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.lookup and the grant must authorize transform.lookup. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.lookup action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `query` (`transform_query`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `transform`
  ;;   (`transform`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "transform.lookup" (func $wr_transform_lookup (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.open. Bound frame set/cache/source/clock-epoch policy.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.open and the grant must authorize transform.open. Applicable grant purposes include
  ;; transform. Depending on the selected inputs and plan, the VM also checks clock.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`), `clock_capability` (`u64`), `clock` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "transform.open" (func $wr_transform_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.publish. Authorize every parent/child and source; nonzero expected_generation fences
  ;; the whole batch. Actual static replacement requires a matching nonzero generation and exact
  ;; transform.static.replace action; zero permits only additions or unchanged static replay.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.publish and the grant must authorize transform.publish. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.publish action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `buffer` (`u64`), `expected_generation` (`u64`), `transforms`
  ;;   (`array<transform>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "transform.publish" (func $wr_transform_publish (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.submit. Owned asynchronous wait binds exact clock epoch and query.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.submit and the grant must authorize transform.submit. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.submit action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `buffer` (`u64`), `query` (`transform_query`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "transform.submit" (func $wr_transform_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.take. Nonconsuming failed copy of one owned query result.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.take and the grant must authorize transform.take. Applicable grant purposes include
  ;; transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.take action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `transform` (`optional<transform>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "transform.take" (func $wr_transform_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; transform.velocity. Advanced time/reference-point operation with all frame/window checks.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; transform.velocity and the grant must authorize transform.velocity. Applicable grant purposes
  ;; include transform.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the transform.velocity action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `buffer` (`u64`),
  ;;   `query` (`velocity_query`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   79656 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `velocity`
  ;;   (`velocity`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "transform.velocity" (func $wr_transform_velocity (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; type.describe. Bounded immutable approved schema dependency closure; type names never load code.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose type.describe
  ;; and the grant must authorize type.describe. Applicable grant purposes include type.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the type.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `identity` (`text`),
  ;;   `cursor` (`optional<u64>`), `limit` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `schema` (`message`),
  ;;   `page` (`page`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "type.describe" (func $wr_type_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; vm.describe. Return only closed VM build-support flags, selected compiler, compile-thread
  ;; ceiling and counts of registered declaration kinds. These are not live thread counts or
  ;; per-module execution permissions. Require independent vm/runtime/metadata authority and exact
  ;; exposure. Self permission.report and module grants cannot authorize VM observation. No module
  ;; names, paths, process IDs, addresses, source bytes or credentials are returned. Carrier
  ;; capability must be zero. Exact immediate caller identity comes from the runtime. Observation
  ;; never freezes deployment, enrolls a caller, opens a capability, replenishes or consumes
  ;; execution quotas, starts a provider, invokes an export, reads foreign memory, or changes another
  ;; policy. A denial writes neither result nor length. Owned temporary buffers are securely
  ;; overwritten.
  ;;
  ;; The caller's deployment must expose vm.describe. The request alias must select a
  ;; vm/runtime/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output.
  (import "uwvm_ros_v2" "vm.describe" (func $wr_vm_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

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

  (export "abi" (func $wr_abi))
  (export "action.cancel" (func $wr_action_cancel))
  (export "action.cancel.set" (func $wr_action_cancel_set))
  (export "action.describe" (func $wr_action_describe))
  (export "action.open" (func $wr_action_open))
  (export "action.respond" (func $wr_action_respond))
  (export "action.submit" (func $wr_action_submit))
  (export "action.take" (func $wr_action_take))
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
  (export "bridge.create" (func $wr_bridge_create))
  (export "bridge.describe" (func $wr_bridge_describe))
  (export "bridge.start" (func $wr_bridge_start))
  (export "bridge.stop" (func $wr_bridge_stop))
  (export "buffer.create" (func $wr_buffer_create))
  (export "buffer.describe" (func $wr_buffer_describe))
  (export "buffer.read" (func $wr_buffer_read))
  (export "buffer.seal" (func $wr_buffer_seal))
  (export "buffer.write" (func $wr_buffer_write))
  (export "capability.close" (func $wr_capability_close))
  (export "capability.open" (func $wr_capability_open))
  (export "capability.revoke" (func $wr_capability_revoke))
  (export "clock.create" (func $wr_clock_create))
  (export "clock.read" (func $wr_clock_read))
  (export "clock.update" (func $wr_clock_update))
  (export "communication.open.cancel" (func $wr_communication_open_cancel))
  (export "communication.open.take" (func $wr_communication_open_take))
  (export "context.describe" (func $wr_context_describe))
  (export "context.open" (func $wr_context_open))
  (export "context.shutdown" (func $wr_context_shutdown))
  (export "control.open" (func $wr_control_open))
  (export "control.result" (func $wr_control_result))
  (export "control.sample" (func $wr_control_sample))
  (export "control.stop" (func $wr_control_stop))
  (export "control.submit" (func $wr_control_submit))
  (export "device.describe" (func $wr_device_describe))
  (export "device.open" (func $wr_device_open))
  (export "device.result" (func $wr_device_result))
  (export "device.stop" (func $wr_device_stop))
  (export "device.submit" (func $wr_device_submit))
  (export "diagnostic.read" (func $wr_diagnostic_read))
  (export "driver.connect" (func $wr_driver_connect))
  (export "driver.describe" (func $wr_driver_describe))
  (export "driver.disconnect" (func $wr_driver_disconnect))
  (export "driver.result" (func $wr_driver_result))
  (export "driver.submit" (func $wr_driver_submit))
  (export "event.stream.close" (func $wr_event_stream_close))
  (export "event.stream.open" (func $wr_event_stream_open))
  (export "event.stream.poll" (func $wr_event_stream_poll))
  (export "graph.snapshot" (func $wr_graph_snapshot))
  (export "graph.watch" (func $wr_graph_watch))
  (export "guard.create" (func $wr_guard_create))
  (export "guard.take" (func $wr_guard_take))
  (export "guard.trigger" (func $wr_guard_trigger))
  (export "lifecycle.open" (func $wr_lifecycle_open))
  (export "lifecycle.respond" (func $wr_lifecycle_respond))
  (export "lifecycle.state" (func $wr_lifecycle_state))
  (export "lifecycle.submit" (func $wr_lifecycle_submit))
  (export "lifecycle.take" (func $wr_lifecycle_take))
  (export "lifecycle.transitions" (func $wr_lifecycle_transitions))
  (export "log.emit" (func $wr_log_emit))
  (export "media.close" (func $wr_media_close))
  (export "media.open" (func $wr_media_open))
  (export "media.submit" (func $wr_media_submit))
  (export "media.take" (func $wr_media_take))
  (export "model.cancel" (func $wr_model_cancel))
  (export "model.describe" (func $wr_model_describe))
  (export "model.open" (func $wr_model_open))
  (export "model.submit" (func $wr_model_submit))
  (export "model.take" (func $wr_model_take))
  (export "module.call.acknowledge" (func $wr_module_call_acknowledge))
  (export "module.call.cancel" (func $wr_module_call_cancel))
  (export "module.call.respond" (func $wr_module_call_respond))
  (export "module.call.result" (func $wr_module_call_result))
  (export "module.call.submit" (func $wr_module_call_submit))
  (export "module.call.take" (func $wr_module_call_take))
  (export "module.describe" (func $wr_module_describe))
  (export "module.exports" (func $wr_module_exports))
  (export "module.group" (func $wr_module_group))
  (export "module.importers" (func $wr_module_importers))
  (export "module.imports" (func $wr_module_imports))
  (export "module.permission.report" (func $wr_module_permission_report))
  (export "node.describe" (func $wr_node_describe))
  (export "node.open" (func $wr_node_open))
  (export "parameter.declare" (func $wr_parameter_declare))
  (export "parameter.describe" (func $wr_parameter_describe))
  (export "parameter.exists" (func $wr_parameter_exists))
  (export "parameter.get" (func $wr_parameter_get))
  (export "parameter.list" (func $wr_parameter_list))
  (export "parameter.open" (func $wr_parameter_open))
  (export "parameter.respond" (func $wr_parameter_respond))
  (export "parameter.search" (func $wr_parameter_search))
  (export "parameter.set" (func $wr_parameter_set))
  (export "parameter.set.atomic" (func $wr_parameter_set_atomic))
  (export "parameter.take" (func $wr_parameter_take))
  (export "parameter.undeclare" (func $wr_parameter_undeclare))
  (export "permission.report" (func $wr_permission_report))
  (export "proposal.accept" (func $wr_proposal_accept))
  (export "proposal.capture" (func $wr_proposal_capture))
  (export "proposal.publish" (func $wr_proposal_publish))
  (export "proposal.read" (func $wr_proposal_read))
  (export "qos.acknowledgements.wait" (func $wr_qos_acknowledgements_wait))
  (export "qos.describe" (func $wr_qos_describe))
  (export "qos.liveliness.assert" (func $wr_qos_liveliness_assert))
  (export "recording.append" (func $wr_recording_append))
  (export "recording.checkpoint" (func $wr_recording_checkpoint))
  (export "recording.open" (func $wr_recording_open))
  (export "recording.stop" (func $wr_recording_stop))
  (export "replay.open" (func $wr_replay_open))
  (export "replay.read" (func $wr_replay_read))
  (export "replay.seek" (func $wr_replay_seek))
  (export "request.describe" (func $wr_request_describe))
  (export "request.release" (func $wr_request_release))
  (export "resource.close" (func $wr_resource_close))
  (export "sensor.describe" (func $wr_sensor_describe))
  (export "sensor.open" (func $wr_sensor_open))
  (export "sensor.take" (func $wr_sensor_take))
  (export "service.abandon" (func $wr_service_abandon))
  (export "service.acknowledge" (func $wr_service_acknowledge))
  (export "service.available" (func $wr_service_available))
  (export "service.describe" (func $wr_service_describe))
  (export "service.open" (func $wr_service_open))
  (export "service.release" (func $wr_service_release))
  (export "service.reserve" (func $wr_service_reserve))
  (export "service.respond" (func $wr_service_respond))
  (export "service.submit" (func $wr_service_submit))
  (export "service.take" (func $wr_service_take))
  (export "timer.cancel" (func $wr_timer_cancel))
  (export "timer.create" (func $wr_timer_create))
  (export "timer.reset" (func $wr_timer_reset))
  (export "timer.take" (func $wr_timer_take))
  (export "topic.acknowledge" (func $wr_topic_acknowledge))
  (export "topic.describe" (func $wr_topic_describe))
  (export "topic.open" (func $wr_topic_open))
  (export "topic.publish" (func $wr_topic_publish))
  (export "topic.release" (func $wr_topic_release))
  (export "topic.reserve" (func $wr_topic_reserve))
  (export "topic.take" (func $wr_topic_take))
  (export "transform.available" (func $wr_transform_available))
  (export "transform.cancel" (func $wr_transform_cancel))
  (export "transform.clear" (func $wr_transform_clear))
  (export "transform.lookup" (func $wr_transform_lookup))
  (export "transform.open" (func $wr_transform_open))
  (export "transform.publish" (func $wr_transform_publish))
  (export "transform.submit" (func $wr_transform_submit))
  (export "transform.take" (func $wr_transform_take))
  (export "transform.velocity" (func $wr_transform_velocity))
  (export "type.describe" (func $wr_type_describe))
  (export "vm.describe" (func $wr_vm_describe))
  (export "wait.acknowledge" (func $wr_wait_acknowledge))
  (export "wait.add" (func $wr_wait_add))
  (export "wait.create" (func $wr_wait_create))
  (export "wait.poll" (func $wr_wait_poll))
  (export "wait.remove" (func $wr_wait_remove))
)
