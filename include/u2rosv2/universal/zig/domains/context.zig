//! ROSv2 context imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"context.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"context.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"context.shutdown"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// context.describe. Sanitized context identity, supported features and shutdown state. Provider
/// feature reporting distinguishes configured, native-attested supported and currently available
/// states; missing/failed native feature probes are not affirmative support.
/// The caller must belong to the capability's environment. The deployment must expose context.describe
/// and the grant must authorize context.describe. Applicable grant purposes include context.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the context.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `context` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `profile` (`profile`), `state`
/// (`text`), `generation` (`u64`), `features` (`array<provider_feature>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"context.describe";

/// context.open. Create an independently owned context only after complete provider/security closure
/// validation.
/// The caller must belong to the capability's environment. The deployment must expose context.open and
/// the grant must authorize context.open. Applicable grant purposes include context.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the context.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"context.open";

/// context.shutdown. Cancel owned work and wake waits; never process exit.
/// The caller must belong to the capability's environment. The deployment must expose context.shutdown
/// and the grant must authorize context.shutdown. Applicable grant purposes include context.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the context.shutdown action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `context`
/// (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const shutdown = raw.@"context.shutdown";
