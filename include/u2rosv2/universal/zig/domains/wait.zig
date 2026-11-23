//! ROSv2 wait imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"wait.acknowledge"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"wait.add"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"wait.create"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"wait.poll"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"wait.remove"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// wait.acknowledge. Acknowledge source sequence; readiness is not data consumption.
/// The caller must belong to the capability's environment. The deployment must expose wait.acknowledge
/// and the grant must authorize wait.acknowledge. Applicable grant purposes include wait.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the wait.acknowledge action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `waitset` (`u64`), `source` (`u64`),
/// `sequence` (`u64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const acknowledge = raw.@"wait.acknowledge";

/// wait.add. Source requires independent resource.observe; bounded membership.
/// The caller must belong to the capability's environment. The deployment must expose wait.add and the
/// grant must authorize wait.add. Applicable grant purposes include wait. Depending on the selected
/// inputs and plan, the VM also checks resource.observe.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the wait.add action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `waitset` (`u64`),
/// `source_capability` (`u64`), `source` (`u64`), `interests` (`u64`), `token` (`u64`).
/// `size` — Exact request length, 40 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const add = raw.@"wait.add";

/// wait.create. Create empty owned waitset.
/// The caller must belong to the capability's environment. The deployment must expose wait.create and
/// the grant must authorize wait.create. Applicable grant purposes include wait.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the wait.create action in the caller's environment.
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
pub const create = raw.@"wait.create";

/// wait.poll. Nonconsuming bounded readiness; infinite wait explicit; authority revalidated after wake.
/// The caller must belong to the capability's environment. The deployment must expose wait.poll and the
/// grant must authorize wait.poll. Applicable grant purposes include wait.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the wait.poll action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `waitset` (`u64`), `duration_ns`
/// (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `records` (`array<ready_record>`).
/// Each 32-byte record contains source, token, events and sequence, with no array length prefix.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const poll = raw.@"wait.poll";

/// wait.remove. Detach exact source from owned waitset.
/// The caller must belong to the capability's environment. The deployment must expose wait.remove and
/// the grant must authorize wait.remove. Applicable grant purposes include wait.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the wait.remove action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `waitset` (`u64`), `source` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const remove = raw.@"wait.remove";
