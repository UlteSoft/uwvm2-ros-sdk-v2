//! ROSv2 control imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"control.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"control.result"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"control.sample"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"control.stop"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"control.submit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// control.open. Reserve complete continuous cycle and safe-state contract.
/// The caller must belong to the capability's environment. The deployment must expose control.open and
/// the grant must authorize control.open. Applicable grant purposes include control. Depending on the
/// selected inputs and plan, the VM also checks device.submit, device.stop, resource.observe,
/// buffer.read, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the control.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`),
/// `device_capability` (`u64`), `device` (`u64`), `sources` (`array<control_source>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `opened` (`control_opening`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4096. The fixed result occupies
/// 32 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"control.open";

/// control.result. Report actual execution, missed phase and watchdog outcome.
/// The caller must belong to the capability's environment. The deployment must expose control.result
/// and the grant must authorize control.result. Applicable grant purposes include control. Depending on
/// the selected inputs and plan, the VM also checks device.submit, device.stop, resource.observe,
/// buffer.read, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the control.result action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `cycle` (`u64`), `sequence` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4096.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const result = raw.@"control.result";

/// control.sample. A bounded input/read phase tied to write deadline and sequence.
/// The caller must belong to the capability's environment. The deployment must expose control.sample
/// and the grant must authorize control.sample. Applicable grant purposes include control. Depending on
/// the selected inputs and plan, the VM also checks device.submit, device.stop, resource.observe,
/// buffer.read, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the control.sample action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `cycle` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `sample` (`cycle_sample`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4096.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const sample = raw.@"control.sample";

/// control.stop. Drain or qualified safe stop; revoke never disables watchdog.
/// The caller must belong to the capability's environment. The deployment must expose control.stop and
/// the grant must authorize control.stop. Applicable grant purposes include control.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the control.stop action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `cycle`
/// (`u64`), `profile` (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4096.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const stop = raw.@"control.stop";

/// control.submit. Check same cycle/sequence/deadline; no attenuation skips an admitted phase.
/// The caller must belong to the capability's environment. The deployment must expose control.submit
/// and the grant must authorize control.submit. Applicable grant purposes include control. Depending on
/// the selected inputs and plan, the VM also checks device.submit, device.stop, resource.observe,
/// buffer.read, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the control.submit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `cycle`
/// (`u64`), `sequence` (`u64`), `controller_epoch` (`u64`), `schema` (`profile`), `command`
/// (`message`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4096.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const submit = raw.@"control.submit";
