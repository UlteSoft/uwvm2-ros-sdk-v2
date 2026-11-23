//! ROSv2 resource imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"resource.close"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// resource.close. Close an owned local scheduling, lifecycle, sealed-buffer, model or transform
/// resource according to its cleanup contract. Retained borrows or cleanup debt retain their capacity
/// until actual retirement; closure does not grant another purpose. Sensor/proposal and
/// recording/replay handles route to their owning dispatchers; retained borrows/pins still prevent
/// premature retirement.
/// The caller must belong to the capability's environment. The deployment must expose resource.close
/// and the grant must authorize resource.close. The resource registry checks the originating grant and
/// provider binding.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the resource.close action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `resource` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the checked reply range. This operation has an empty reply body.
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 0 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. The VM writes a zero length before the mutation.
/// A later refusal can therefore also leave zero in the slot.
pub const close = raw.@"resource.close";
