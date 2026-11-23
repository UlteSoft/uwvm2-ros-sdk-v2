//! ROSv2 clock imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"clock.create"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"clock.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"clock.update"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// clock.create. Kind must match exact clock purpose.
/// The caller must belong to the capability's environment. The deployment must expose clock.create and
/// the grant must authorize clock.create. Applicable grant purposes include clock.steady, clock.system,
/// clock.ros.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the clock.create action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `kind` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `resource` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const create = raw.@"clock.create";

/// clock.read. Sample owned clock; unstarted time remains flagged.
/// The caller must belong to the capability's environment. The deployment must expose clock.read and
/// the grant must authorize clock.read. Applicable grant purposes include clock.steady, clock.system,
/// clock.ros.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the clock.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `clock` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `now` (`i64`), `epoch` (`u64`),
/// `started` (`bool`), `kind` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 32 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"clock.read";

/// clock.update. ROS clock source must independently permit clock.read with matching resource and
/// binding.
/// The caller must belong to the capability's environment. The deployment must expose clock.update and
/// the grant must authorize clock.update. Applicable grant purposes include clock.ros. Depending on the
/// selected inputs and plan, the VM also checks clock.read.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the clock.update action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `source_capability` (`u64`), `clock`
/// (`u64`), `now` (`i64`), `started` (`bool`).
/// `size` — Exact request length, 32 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const update = raw.@"clock.update";
