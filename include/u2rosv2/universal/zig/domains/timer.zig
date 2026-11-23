//! ROSv2 timer imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"timer.cancel"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"timer.create"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"timer.reset"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"timer.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// timer.cancel. Disarm owned timer and notify waiters.
/// The caller must belong to the capability's environment. The deployment must expose timer.cancel and
/// the grant must authorize timer.cancel. Applicable grant purposes include timer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the timer.cancel action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `timer` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const cancel = raw.@"timer.cancel";

/// timer.create. Clock dependency needs independent read grant.
/// The caller must belong to the capability's environment. The deployment must expose timer.create and
/// the grant must authorize timer.create. Applicable grant purposes include timer. Depending on the
/// selected inputs and plan, the VM also checks clock.read.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the timer.create action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `clock_capability` (`u64`), `clock`
/// (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `resource` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const create = raw.@"timer.create";

/// timer.reset. Overflow-checked schedule; zero period is one-shot.
/// The caller must belong to the capability's environment. The deployment must expose timer.reset and
/// the grant must authorize timer.reset. Applicable grant purposes include timer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the timer.reset action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `timer` (`u64`), `due` (`i64`),
/// `period` (`i64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const reset = raw.@"timer.reset";

/// timer.take. Coalesced occurrence record consumed only after delivery.
/// The caller must belong to the capability's environment. The deployment must expose timer.take and
/// the grant must authorize timer.take. Applicable grant purposes include timer.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the timer.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `timer` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `expected` (`i64`), `actual` (`i64`),
/// `occurrences` (`u64`), `clock_epoch` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 32 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"timer.take";
