//! ROSv2 buffer imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"buffer.create"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"buffer.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"buffer.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"buffer.seal"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"buffer.write"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// buffer.create. Reserve bounded data/workspace before publication.
/// The caller must belong to the capability's environment. The deployment must expose buffer.create and
/// the grant must authorize buffer.create. Applicable grant purposes include buffer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the buffer.create action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `layout` (`buffer_layout`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194328 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194816. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const create = raw.@"buffer.create";

/// buffer.describe. Untrusted origin cannot be relabelled as a trusted sensor.
/// The caller must belong to the capability's environment. The deployment must expose buffer.describe
/// and the grant must authorize buffer.describe. Applicable grant purposes include buffer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the buffer.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `layout` (`buffer_layout`), `sealed`
/// (`bool`), `provenance` (`text`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194816.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"buffer.describe";

/// buffer.read. Exact bounded read; no host descriptor export.
/// The caller must belong to the capability's environment. The deployment must expose buffer.read and
/// the grant must authorize buffer.read. Applicable grant purposes include buffer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the buffer.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `offset` (`u64`),
/// `bytes` (`u64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the writable result. Wire order is `data` (`bytes`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194816.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"buffer.read";

/// buffer.seal. Immutable publication with digest and registered layout.
/// The caller must belong to the capability's environment. The deployment must expose buffer.seal and
/// the grant must authorize buffer.seal. Applicable grant purposes include buffer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the buffer.seal action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `digest`
/// (`bytes`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194328 bytes.
/// `output` — Guest address of the writable result. Wire order is `reference` (`buffer_ref`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194816. The fixed result
/// occupies 16 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const seal = raw.@"buffer.seal";

/// buffer.write. Contiguous bounded write only before seal; no native pointer.
/// The caller must belong to the capability's environment. The deployment must expose buffer.write and
/// the grant must authorize buffer.write. Applicable grant purposes include buffer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the buffer.write action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `expected_offset`
/// (`u64`), `data` (`bytes`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194328 bytes.
/// `output` — Guest address of the writable result. Wire order is `accepted_bytes` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194816. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const write = raw.@"buffer.write";
