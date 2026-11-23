//! ROSv2 proposal imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"proposal.accept"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"proposal.capture"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"proposal.publish"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"proposal.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// proposal.accept. Independent arbiter and exact current target action/argument constraints; cannot
/// broaden rights.
/// The caller must belong to the capability's environment. The deployment must expose proposal.accept
/// and the grant must authorize proposal.accept. Applicable grant purposes include arbiter. Depending
/// on the selected inputs and plan, the VM also checks proposal.read.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the proposal.accept action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`),
/// `proposal_capability` (`u64`), `proposal` (`u64`), `target_capability` (`u64`), `target` (`u64`),
/// `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 8192.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const accept = raw.@"proposal.accept";

/// proposal.capture. Explicit finite capture of actual typed source observations and ordered sealed
/// buffers; exact per-capability key replay. Closing capture releases only its own pins. No model
/// execution or target effect.
/// The caller must belong to the capability's environment. The deployment must expose proposal.capture
/// and the grant must authorize proposal.capture. Applicable grant purposes include proposal. Depending
/// on the selected inputs and plan, the VM also checks resource.observe, buffer.read.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the proposal.capture action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `profile`
/// (`profile`), `sources` (`array<proposal_capture_source>`), `expiry` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `capture` (`u64`), `inputs`
/// (`array<proposal_captured_buffer>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 8192.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const capture = raw.@"proposal.capture";

/// proposal.publish. Authenticate complete successful terminal output from the actual model request
/// against original captured input IDs, SHA and order. Independently authorize publication; model bytes
/// cannot issue grants or execute tools.
/// The caller must belong to the capability's environment. The deployment must expose proposal.publish
/// and the grant must authorize proposal.publish. Applicable grant purposes include proposal. Depending
/// on the selected inputs and plan, the VM also checks model.take.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the proposal.publish action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `capture`
/// (`u64`), `model_request` (`u64`), `envelope` (`bytes`), `expiry` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 16384 bytes.
/// `output` — Guest address of the writable result. Wire order is `proposal` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 8192. The fixed result occupies
/// 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const publish = raw.@"proposal.publish";

/// proposal.read. Read inert validated model proposal and trusted provenance.
/// The caller must belong to the capability's environment. The deployment must expose proposal.read and
/// the grant must authorize proposal.read. Applicable grant purposes include proposal.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the proposal.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `proposal` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `proposal` (`proposal`).
/// `capacity` — Byte capacity of the full writable reply range, at most 8192.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"proposal.read";
