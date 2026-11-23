//! ROSv2 event imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"event.stream.close"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"event.stream.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"event.stream.poll"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// event.stream.close. Detach exact stream and wake waiters without closing sources.
/// The caller must belong to the capability's environment. The deployment must expose
/// event.stream.close and the grant must authorize event.stream.close. Applicable grant purposes
/// include event.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the event.stream.close action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `stream` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `closed` (`bool`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const stream_close = raw.@"event.stream.close";

/// event.stream.open. Authorize each observed source and field policy; source references use
/// capability/resource pair.
/// The caller must belong to the capability's environment. The deployment must expose event.stream.open
/// and the grant must authorize event.stream.open. Applicable grant purposes include event. Depending
/// on the selected inputs and plan, the VM also checks resource.observe.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the event.stream.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `sources` (`array<source_ref>`),
/// `profile` (`profile`), `capacity` (`capacity`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const stream_open = raw.@"event.stream.open";

/// event.stream.poll. Copy complete records before consumption; explicit loss and generation; bounded
/// steady deadline.
/// The caller must belong to the capability's environment. The deployment must expose event.stream.poll
/// and the grant must authorize event.stream.poll. Applicable grant purposes include event. Depending
/// on the selected inputs and plan, the VM also checks resource.observe.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the event.stream.poll action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `stream` (`u64`), `limit` (`u64`),
/// `deadline` (`u64`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the writable result. Wire order is `events` (`array<event_record>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const stream_poll = raw.@"event.stream.poll";
