"""Raw guard imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_guard_create(cap, memory, request, size, output, capacity, length_output):
    """Create owned guard, rollback if handle delivery fails.

    The caller must belong to the capability's environment. The deployment must expose
    guard.create and the grant must authorize guard.create. Applicable grant purposes include
    guard.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the guard.create action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the checked zero-length request range.

    size (i64, unsigned bit pattern). Exact request length, 0 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `resource` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('guard.create', cap, memory, request, size, output, capacity, length_output)


def wr_guard_take(cap, memory, request, size, output, capacity, length_output):
    """Consume pending count only after checked delivery.

    The caller must belong to the capability's environment. The deployment must expose
    guard.take and the grant must authorize guard.take. Applicable grant purposes include guard.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the guard.take action in the caller's
    environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `guard` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `count` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('guard.take', cap, memory, request, size, output, capacity, length_output)


def wr_guard_trigger(cap, memory, request, size, output, capacity, length_output):
    """Increment guard generation under exact owner grant.

    The caller must belong to the capability's environment. The deployment must expose
    guard.trigger and the grant must authorize guard.trigger. Applicable grant purposes include
    guard.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the guard.trigger action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `guard` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('guard.trigger', cap, memory, request, size, output, capacity, length_output)
