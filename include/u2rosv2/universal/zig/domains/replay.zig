//! ROSv2 replay imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"replay.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"replay.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"replay.seek"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// replay.open. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only and
/// never publishes or changes clocks.
/// The caller must belong to the capability's environment. The deployment must expose replay.open and
/// the grant must authorize replay.open. Applicable grant purposes include replay. Depending on the
/// selected inputs and plan, the VM also checks resource.observe, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the replay.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `source_capability` (`u64`),
/// `profile` (`profile`), `objects` (`array<recording_object>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 6072 bytes.
/// `output` — Guest address of the writable result. Wire order is `replay` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"replay.open";

/// replay.read. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only and
/// never publishes or changes clocks.
/// The caller must belong to the capability's environment. The deployment must expose replay.read and
/// the grant must authorize replay.read. Applicable grant purposes include replay. Depending on the
/// selected inputs and plan, the VM also checks resource.observe, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the replay.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `replay` (`u64`), `limit` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `ordinal` (`u64`), `records`
/// (`array<recording_message>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"replay.read";

/// replay.seek. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Replay uses an explicitly granted fixed source and exact object digests; it returns bytes only and
/// never publishes or changes clocks.
/// The caller must belong to the capability's environment. The deployment must expose replay.seek and
/// the grant must authorize replay.seek. Applicable grant purposes include replay. Depending on the
/// selected inputs and plan, the VM also checks resource.observe, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the replay.seek action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `replay` (`u64`), `ordinal` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `ordinal` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const seek = raw.@"replay.seek";
