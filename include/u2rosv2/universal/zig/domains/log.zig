//! ROSv2 log imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"log.emit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// log.emit. Independent log grant, bounded private content and declared attenuation; no format-string
/// execution.
/// The caller must belong to the capability's environment. The deployment must expose log.emit and the
/// grant must authorize log.emit. Applicable grant purposes include log.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the log.emit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `session` (`u64`), `sequence`
/// (`u64`), `severity` (`text`), `logger` (`text`), `stamp` (`optional<log_stamp>`), `message`
/// (`text`), `location` (`optional<log_location>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`log_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 48 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const emit = raw.@"log.emit";
