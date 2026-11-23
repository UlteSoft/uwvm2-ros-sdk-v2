//! ROSv2 diagnostic imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"diagnostic.read"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// diagnostic.read. Bounded metadata counters, denial/loss/timeout/provider states; content inspection
/// separate.
/// The caller must belong to the capability's environment. The deployment must expose diagnostic.read
/// and the grant must authorize diagnostic.read. Applicable grant purposes include diagnostic.
/// Depending on the selected inputs and plan, the VM also checks resource.observe.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the diagnostic.read action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `source_capability`
/// (`u64`), `cursor` (`optional<u64>`), `limit` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 40 bytes.
/// `output` — Guest address of the writable result. Wire order is `page` (`diagnostic_page`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const read = raw.@"diagnostic.read";
