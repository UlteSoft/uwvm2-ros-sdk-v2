//! ROSv2 transform imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"transform.available"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.cancel"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.clear"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.lookup"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.publish"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.submit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"transform.velocity"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// transform.available. Same visibility boundary as lookup; no hidden frame existence leak.
/// The caller must belong to the capability's environment. The deployment must expose
/// transform.available and the grant must authorize transform.available. Applicable grant purposes
/// include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.available action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `query`
/// (`transform_query`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `available` (`bool`), `reason`
/// (`text`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const available = raw.@"transform.available";

/// transform.cancel. Cancel owned query and wake waiters.
/// The caller must belong to the capability's environment. The deployment must expose transform.cancel
/// and the grant must authorize transform.cancel. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.cancel action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `request` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const cancel = raw.@"transform.cancel";

/// transform.clear. Explicit history mutation and pending query invalidation; static policy separate.
/// The caller must belong to the capability's environment. The deployment must expose transform.clear
/// and the grant must authorize transform.clear. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.clear action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `buffer`
/// (`u64`), `expected_generation` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const clear = raw.@"transform.clear";

/// transform.lookup. Enforce all query-path frames, epochs and cache bounds.
/// The caller must belong to the capability's environment. The deployment must expose transform.lookup
/// and the grant must authorize transform.lookup. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.lookup action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `query`
/// (`transform_query`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `transform` (`transform`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const lookup = raw.@"transform.lookup";

/// transform.open. Bound frame set/cache/source/clock-epoch policy.
/// The caller must belong to the capability's environment. The deployment must expose transform.open
/// and the grant must authorize transform.open. Applicable grant purposes include transform. Depending
/// on the selected inputs and plan, the VM also checks clock.read.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`),
/// `clock_capability` (`u64`), `clock` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"transform.open";

/// transform.publish. Authorize every parent/child and source; nonzero expected_generation fences the
/// whole batch. Actual static replacement requires a matching nonzero generation and exact
/// transform.static.replace action; zero permits only additions or unchanged static replay.
/// The caller must belong to the capability's environment. The deployment must expose transform.publish
/// and the grant must authorize transform.publish. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.publish action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `buffer`
/// (`u64`), `expected_generation` (`u64`), `transforms` (`array<transform>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const publish = raw.@"transform.publish";

/// transform.submit. Owned asynchronous wait binds exact clock epoch and query.
/// The caller must belong to the capability's environment. The deployment must expose transform.submit
/// and the grant must authorize transform.submit. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.submit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `buffer`
/// (`u64`), `query` (`transform_query`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const submit = raw.@"transform.submit";

/// transform.take. Nonconsuming failed copy of one owned query result.
/// The caller must belong to the capability's environment. The deployment must expose transform.take
/// and the grant must authorize transform.take. Applicable grant purposes include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `request` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`), `transform`
/// (`optional<transform>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const take = raw.@"transform.take";

/// transform.velocity. Advanced time/reference-point operation with all frame/window checks.
/// The caller must belong to the capability's environment. The deployment must expose
/// transform.velocity and the grant must authorize transform.velocity. Applicable grant purposes
/// include transform.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the transform.velocity action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `buffer` (`u64`), `query`
/// (`velocity_query`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 79656 bytes.
/// `output` — Guest address of the writable result. Wire order is `velocity` (`velocity`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 48 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const velocity = raw.@"transform.velocity";
