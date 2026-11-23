"""Raw lifecycle imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_lifecycle_open(cap, memory, request, size, output, capacity, length_output):
    """Open one explicitly permitted client=1/server=2 role in a deployed local-lifecycle alias; no
    native node or actuator authority. Opening never resets state or history.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.open and the grant must authorize lifecycle.open. Applicable grant purposes
    include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `role` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.open', cap, memory, request, size, output, capacity, length_output)


def wr_lifecycle_respond(cap, memory, request, size, output, capacity, length_output):
    """Resolve only an exactly delivered matching request/generation using ROS outcome97/98/99.
    Preserve last exact response receipt; error queues error-processing callback. No native
    callback execution.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.respond and the grant must authorize lifecycle.respond. Applicable grant purposes
    include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.respond action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `handle` (`u64`), `request` (`u64`), `expected_generation` (`u64`), `outcome` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 32 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `key` (`u64`), `request` (`u64`), `generation` (`u64`), `state` (`u64`), `status` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 40 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.respond', cap, memory, request, size, output, capacity, length_output)


def wr_lifecycle_state(cap, memory, request, size, output, capacity, length_output):
    """Observe owned cached logical state and enforce an expired finite deadline on access; no
    physical or autonomous stop guarantee.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.state and the grant must authorize lifecycle.state. Applicable grant purposes
    include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.state action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `handle` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `state` (`u64`), `generation` (`u64`), `request` (`u64`), `transition` (`u64`), `deadline`
    (`u64`), `status` (`u64`), `delivered` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 56 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.state', cap, memory, request, size, output, capacity, length_output)


def wr_lifecycle_submit(cap, memory, request, size, output, capacity, length_output):
    """Exactly ordered successful-submission keys with original receipt replay, finite absolute
    steady deadline, expected generation and one pending callback. Rejected submissions do not
    consume key.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.submit and the grant must authorize lifecycle.submit. Applicable grant purposes
    include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.submit action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `handle` (`u64`), `key` (`u64`), `transition` (`u64`), `expected_generation` (`u64`),
    `deadline` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 40 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `key` (`u64`), `request` (`u64`), `generation` (`u64`), `state` (`u64`), `status` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 40 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.submit', cap, memory, request, size, output, capacity, length_output)


def wr_lifecycle_take(cap, memory, request, size, output, capacity, length_output):
    """Reserve one callback, release provider lock before checked delivery, then revalidate
    owner/request/generation/deadline before marking delivered. Failed delivery is not consumed.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.take and the grant must authorize lifecycle.take. Applicable grant purposes
    include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.take action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `handle` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `request` (`u64`), `transition` (`u64`), `generation` (`u64`), `phase` (`u64`), `deadline`
    (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 40 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.take', cap, memory, request, size, output, capacity, length_output)


def wr_lifecycle_transitions(cap, memory, request, size, output, capacity, length_output):
    """Return only currently legal and deployment-permitted transition bits; no transition
    authority is granted.

    The caller must belong to the capability's environment. The deployment must expose
    lifecycle.transitions and the grant must authorize lifecycle.transitions. Applicable grant
    purposes include lifecycle.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the lifecycle.transitions action in
    the caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `handle` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `allowed_mask` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('lifecycle.transitions', cap, memory, request, size, output, capacity, length_output)
