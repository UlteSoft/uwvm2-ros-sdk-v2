//! ROSv2 graph imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"graph.snapshot"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"graph.watch"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// graph.snapshot. Exact filtered discovery through an explicitly owned observer node and context;
/// observer node profile and actual parent context must match, with counted attachment capacity and
/// complete origin authority.
/// The caller must belong to the capability's environment. The deployment must expose graph.snapshot
/// and the grant must authorize graph.snapshot. Applicable grant purposes include discovery. Depending
/// on the selected inputs and plan, the VM also checks context.describe, node.open, context.open.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the graph.snapshot action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `context_capability` (`u64`),
/// `context` (`u64`), `observer_node_capability` (`u64`), `observer_node` (`u64`), `profile`
/// (`profile`), `cursor` (`optional<u64>`), `limit` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `page` (`page`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const snapshot = raw.@"graph.snapshot";

/// graph.watch. Exact filtered discovery through an explicitly owned observer node and context;
/// observer node profile and actual parent context must match, with counted attachment capacity and
/// complete origin authority.
/// The caller must belong to the capability's environment. The deployment must expose graph.watch and
/// the grant must authorize graph.watch. Applicable grant purposes include discovery. Depending on the
/// selected inputs and plan, the VM also checks context.describe, node.open, context.open.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the graph.watch action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `context_capability` (`u64`),
/// `context` (`u64`), `observer_node_capability` (`u64`), `observer_node` (`u64`), `profile`
/// (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const watch = raw.@"graph.watch";
