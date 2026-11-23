//! ROSv2 guard imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"guard.create"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"guard.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"guard.trigger"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// guard.create. Create owned guard, rollback if handle delivery fails.
/// The caller must belong to the capability's environment. The deployment must expose guard.create and
/// the grant must authorize guard.create. Applicable grant purposes include guard.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the guard.create action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the checked zero-length request range.
/// `size` — Exact request length, 0 bytes.
/// `output` — Guest address of the writable result. Wire order is `resource` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const create = raw.@"guard.create";

/// guard.take. Consume pending count only after checked delivery.
/// The caller must belong to the capability's environment. The deployment must expose guard.take and
/// the grant must authorize guard.take. Applicable grant purposes include guard.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the guard.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `guard` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `count` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"guard.take";

/// guard.trigger. Increment guard generation under exact owner grant.
/// The caller must belong to the capability's environment. The deployment must expose guard.trigger and
/// the grant must authorize guard.trigger. Applicable grant purposes include guard.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the guard.trigger action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `guard` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const trigger = raw.@"guard.trigger";
