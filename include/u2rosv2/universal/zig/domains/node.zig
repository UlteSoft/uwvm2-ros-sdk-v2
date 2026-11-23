//! ROSv2 node imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"node.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"node.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// node.describe. Only owned resolved identity and enabled features.
/// The caller must belong to the capability's environment. The deployment must expose node.describe and
/// the grant must authorize node.describe. Applicable grant purposes include node.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the node.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `node` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `name` (`text`), `namespace`
/// (`text`), `profile` (`profile`), `generation` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"node.describe";

/// node.open. Resolve immutable node/name/remapping/profile under exact parent context grant. Creation
/// is asynchronous: explicit monotonically increasing key and finite absolute steady deadline; response
/// is a request receipt, not an endpoint. communication.open.take retrieves a separately published
/// typed handle.
/// The caller must belong to the capability's environment. The deployment must expose node.open and the
/// grant must authorize node.open. Applicable grant purposes include node. Depending on the selected
/// inputs and plan, the VM also checks context.open.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the node.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `context_capability` (`u64`),
/// `context` (`u64`), `profile` (`profile`), `creation_key` (`u64`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `creation`
/// (`communication_creation_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 48 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const open = raw.@"node.open";
