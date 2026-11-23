//! ROSv2 media imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"media.close"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"media.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"media.submit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"media.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// media.close. Only owned stream/viewer; no unrelated listener shutdown.
/// The caller must belong to the capability's environment. The deployment must expose media.close and
/// the grant must authorize media.close. Applicable grant purposes include media.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the media.close action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `stream`
/// (`u64`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4096 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 1024.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const close = raw.@"media.close";

/// media.open. Separate codec/ingress/egress/viewer and listener profile grants.
/// The caller must belong to the capability's environment. The deployment must expose media.open and
/// the grant must authorize media.open. Applicable grant purposes include media. Depending on the
/// selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create, buffer.write,
/// buffer.seal.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the media.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`), `source`
/// (`resource_ref`), `output_capability` (`u64`), `egress` (`optional<resource_ref>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4096 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 1024. The fixed result occupies
/// 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"media.open";

/// media.submit. Bound decoded expansion, encoded output and egress destination.
/// The caller must belong to the capability's environment. The deployment must expose media.submit and
/// the grant must authorize media.submit. Applicable grant purposes include media. Depending on the
/// selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create, buffer.write,
/// buffer.seal.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the media.submit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `stream`
/// (`u64`), `frame` (`buffer_ref`), `description` (`media_frame`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4096 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 1024.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const submit = raw.@"media.submit";

/// media.take. Complete bounded encoded/decoded frame under profile.
/// The caller must belong to the capability's environment. The deployment must expose media.take and
/// the grant must authorize media.take. Applicable grant purposes include media. Depending on the
/// selected inputs and plan, the VM also checks buffer.read, data.export, buffer.create, buffer.write,
/// buffer.seal.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the media.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `stream` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `record` (`media_delivery`).
/// `capacity` — Byte capacity of the full writable reply range, at most 1024.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"media.take";
