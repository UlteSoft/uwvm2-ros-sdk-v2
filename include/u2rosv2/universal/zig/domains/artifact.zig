//! ROSv2 artifact imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"artifact.abort"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.append"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.begin"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.commit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.publish"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.receipt"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.remove"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"artifact.status"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// artifact.abort. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.abort
/// and the grant must authorize artifact.abort. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.abort action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `object` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const abort = raw.@"artifact.abort";

/// artifact.append. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.append
/// and the grant must authorize artifact.append. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.append action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `object` (`u64`),
/// `expected_offset` (`u64`), `data` (`bytes`).
/// `size` — 24 bytes of header plus the raw data byte count, at most 4194328 bytes in total. The data
/// has no length prefix.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const append = raw.@"artifact.append";

/// artifact.begin. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.begin
/// and the grant must authorize artifact.begin. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.begin action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `reservation`
/// (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const begin = raw.@"artifact.begin";

/// artifact.commit. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.commit
/// and the grant must authorize artifact.commit. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.commit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `object` (`u64`),
/// `expected_size` (`u64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const commit = raw.@"artifact.commit";

/// artifact.describe. 64-byte approved metadata: four LE words then raw32 SHA256. Purpose codes1
/// package,2 configuration,3 calibration,4 map,5 model-weights. No source path or FD.
/// The caller must belong to the capability's environment. The deployment must expose artifact.describe
/// and the grant must authorize artifact.describe. Applicable grant purposes include package,
/// configuration, calibration, map, model-weights.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `object` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `generation` (`u64`), `size` (`u64`),
/// `purpose_code` (`u64`), `maximum_transfer` (`u64`), `sha256` (`bytes`). The last 32 bytes are the
/// raw SHA-256 digest.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 64 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"artifact.describe";

/// artifact.open. Exact positive deployment generation and 32 raw SHA256 bytes; sealed-input binding
/// only. Roll back unpublished handles on failed delivery. No output-store read binding.
/// The caller must belong to the capability's environment. The deployment must expose artifact.open and
/// the grant must authorize artifact.open. Applicable grant purposes include package, configuration,
/// calibration, map, model-weights.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `generation` (`u64`), `sha256`
/// (`bytes`). The SHA-256 digest occupies 32 raw bytes immediately after the generation.
/// `size` — Exact request length, 40 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"artifact.open";

/// artifact.publish. Publish one complete bounded volatile object using the existing exact replay
/// stream; all publish/begin/append/commit rights and exposures required; scratch capacity reserved
/// before carrier copying.
/// The caller must belong to the capability's environment. The deployment must expose artifact.publish
/// and the grant must authorize artifact.publish. Applicable grant purposes include cache. Depending on
/// the selected inputs and plan, the VM also checks artifact.begin, artifact.append, artifact.commit.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.publish action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `size` (`u64`),
/// `data` (`bytes`).
/// `size` — 16 bytes of header plus the declared number of raw data bytes. The header check bounds the
/// whole span at 4194328 bytes and the grant additionally bounds the payload.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const publish = raw.@"artifact.publish";

/// artifact.read. Bounded requested bytes from immutable handle and offset; raw output, EOF short read,
/// no cursor. Exact read action; requested bytes cannot exceed configured transfer or output capacity.
/// Published volatile cache objects are also readable under independent cache read authority; staging
/// stays hidden.
/// The caller must belong to the capability's environment. The deployment must expose artifact.read and
/// the grant must authorize artifact.read. Applicable grant purposes include package, configuration,
/// calibration, map, model-weights, cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `object` (`u64`), `offset` (`u64`),
/// `bytes` (`u64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the writable result. Wire order is `data` (`bytes`). The result contains
/// raw data without a length prefix.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"artifact.read";

/// artifact.receipt. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.receipt
/// and the grant must authorize artifact.receipt. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.receipt action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const receipt = raw.@"artifact.receipt";

/// artifact.remove. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.remove
/// and the grant must authorize artifact.remove. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.remove action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`u64`), `object` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const remove = raw.@"artifact.remove";

/// artifact.status. Explicit cache/volatile-output only. Per-alias next-key ACK and exact last-request
/// replay; full begin allocation remains charged until abort/remove. Publication is immutable session
/// data, never durable. Status and receipt queries do not acknowledge. No host path or descriptor.
/// The caller must belong to the capability's environment. The deployment must expose artifact.status
/// and the grant must authorize artifact.status. Applicable grant purposes include cache.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the artifact.status action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `object` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `key` (`u64`), `operation` (`u64`),
/// `object` (`u64`), `effect_status` (`u64`), `accepted_bytes` (`u64`), `total_bytes` (`u64`),
/// `retained_bytes` (`u64`), `state` (`u64`), `flags` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 72 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const status = raw.@"artifact.status";
