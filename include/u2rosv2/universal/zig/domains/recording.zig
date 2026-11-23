//! ROSv2 recording imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"recording.append"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"recording.checkpoint"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"recording.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"recording.stop"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// recording.append. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
/// checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
/// The caller must belong to the capability's environment. The deployment must expose recording.append
/// and the grant must authorize recording.append. Applicable grant purposes include recording.
/// Depending on the selected inputs and plan, the VM also checks buffer.read, data.export.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the recording.append action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `writer` (`u64`), `key` (`u64`),
/// `items` (`array<recording_buffer_item>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 6072 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`recording_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 104 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const append = raw.@"recording.append";

/// recording.checkpoint. Private finite volatile MCAP store with exact deployment channel/buffer
/// profiles, caller incarnation ownership, atomic source read/export authority and retained pinned
/// objects. Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
/// checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
/// The caller must belong to the capability's environment. The deployment must expose
/// recording.checkpoint and the grant must authorize recording.checkpoint. Applicable grant purposes
/// include recording.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the recording.checkpoint action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `writer` (`u64`), `key` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`recording_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 104 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const checkpoint = raw.@"recording.checkpoint";

/// recording.open. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
/// checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
/// The caller must belong to the capability's environment. The deployment must expose recording.open
/// and the grant must authorize recording.open. Applicable grant purposes include recording.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the recording.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `profile` (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 6072 bytes.
/// `output` — Guest address of the writable result. Wire order is `writer` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"recording.open";

/// recording.stop. Private finite volatile MCAP store with exact deployment channel/buffer profiles,
/// caller incarnation ownership, atomic source read/export authority and retained pinned objects.
/// Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
/// checkpoint. Checkpoint is complete volatile acceptance, not durable storage.
/// The caller must belong to the capability's environment. The deployment must expose recording.stop
/// and the grant must authorize recording.stop. Applicable grant purposes include recording.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the recording.stop action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `writer` (`u64`), `key` (`u64`),
/// `drain` (`bool`).
/// `size` — Exact request length, 24 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`recording_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 104 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const stop = raw.@"recording.stop";
