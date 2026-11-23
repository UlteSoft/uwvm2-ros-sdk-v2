//! ROSv2 driver imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"driver.connect"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"driver.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"driver.disconnect"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"driver.result"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"driver.submit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// driver.connect. Perform one nonblocking handshake on a registered inherited channel. Readiness
/// grants no actuation authority; repeated handshake polling never launches code.
/// The caller must belong to the capability's environment. The deployment must expose driver.connect
/// and the grant must authorize driver.connect. Applicable grant purposes include driver.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the driver.connect action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the checked zero-length request range.
/// `size` — Exact request length, 0 bytes.
/// `output` — Guest address of the writable result. Wire order is `connected` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 65552. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const connect = raw.@"driver.connect";

/// driver.describe. Read detached session metadata only; never pump packets, infer physical safety,
/// restart a driver or replenish authority.
/// The caller must belong to the capability's environment. The deployment must expose driver.describe
/// and the grant must authorize driver.describe. Applicable grant purposes include driver.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the driver.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the checked zero-length request range.
/// `size` — Exact request length, 0 bytes.
/// `output` — Guest address of the writable result. Wire order is `state` (`u64`), `sequence` (`u64`),
/// `status` (`u64`), `effect_unknown` (`bool`).
/// `capacity` — Byte capacity of the full writable reply range, at most 65552. The fixed result
/// occupies 32 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"driver.describe";

/// driver.disconnect. Release this connection and erase retained buffers. Best-effort release and local
/// descriptor closure never terminate a shared driver. Independent receiver expiry remains mandatory.
/// The caller must belong to the capability's environment. The deployment must expose driver.disconnect
/// and the grant must authorize driver.disconnect. Applicable grant purposes include driver.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the driver.disconnect action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the checked zero-length request range.
/// `size` — Exact request length, 0 bytes.
/// `output` — Guest address of the writable result. Wire order is `released` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 65552. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const disconnect = raw.@"driver.disconnect";

/// driver.result. Receive an exact sequence and incarnation-bound result. Failed guest delivery retains
/// bytes. Timeout after send fences the session with effect_unknown; never retry a non-idempotent
/// operation automatically.
/// The caller must belong to the capability's environment. The deployment must expose driver.result and
/// the grant must authorize driver.result. Applicable grant purposes include driver.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the driver.result action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `sequence` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `status` (`u64`), `payload`
/// (`bytes`).
/// `capacity` — Byte capacity of the full writable reply range, at most 65552. Reserve 16 bytes plus
/// the route's configured maximum response payload even when the pending response is shorter.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. The response record contains the driver's status and payload.
pub const result = raw.@"driver.result";

/// driver.submit. Submit one bounded fixed-contract request. Exact in-flight retry returns its receipt
/// without resending. Changed bytes or deadline conflict; submission is local transport acceptance,
/// never physical completion.
/// The caller must belong to the capability's environment. The deployment must expose driver.submit and
/// the grant must authorize driver.submit. Applicable grant purposes include driver.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the driver.submit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `sequence` (`u64`), `deadline`
/// (`u64`), `payload` (`bytes`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 65560 bytes.
/// `output` — Guest address of the writable result. Wire order is `sequence` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 65552. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const submit = raw.@"driver.submit";
