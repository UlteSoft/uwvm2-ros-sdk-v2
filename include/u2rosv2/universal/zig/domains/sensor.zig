//! ROSv2 sensor imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"sensor.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"sensor.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"sensor.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// sensor.describe. Bound source identity, loss and negotiated capabilities; no credentials.
/// The caller must belong to the capability's environment. The deployment must expose sensor.describe
/// and the grant must authorize sensor.describe. Applicable grant purposes include sensor.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the sensor.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `sensor` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `profile` (`profile`), `state`
/// (`message`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4196352.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"sensor.describe";

/// sensor.open. Ingress-only approved source/transport/schema/queue; no send/listen authority.
/// The caller must belong to the capability's environment. The deployment must expose sensor.open and
/// the grant must authorize sensor.open. Applicable grant purposes include sensor.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the sensor.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 144 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4196352. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"sensor.open";

/// sensor.take. Validated complete frame with timestamp origin and discontinuity. Capacity for the
/// largest complete frame is checked before native read. The local capture ordinal and optional actual
/// native sequence are distinct. Failed guest copy retains the frame for retry.
/// The caller must belong to the capability's environment. The deployment must expose sensor.take and
/// the grant must authorize sensor.take. Applicable grant purposes include sensor. Depending on the
/// selected inputs and plan, the VM also checks data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the sensor.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `sensor` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `record` (`delivery`), `buffer`
/// (`u64`), `schema` (`profile`), `buffer_profile` (`profile`), `frame` (`text`), `units` (`text`),
/// `source` (`u64`), `native_sequence` (`optional<u64>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4196352.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"sensor.take";
