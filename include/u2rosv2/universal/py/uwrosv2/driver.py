"""Raw driver imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_driver_connect(cap, memory, request, size, output, capacity, length_output):
    """Perform one nonblocking handshake on a registered inherited channel. Readiness grants no
    actuation authority; repeated handshake polling never launches code.

    The caller must belong to the capability's environment. The deployment must expose
    driver.connect and the grant must authorize driver.connect. Applicable grant purposes
    include driver.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the driver.connect action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the checked zero-length request range.

    size (i64, unsigned bit pattern). Exact request length, 0 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `connected` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65552. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('driver.connect', cap, memory, request, size, output, capacity, length_output)


def wr_driver_describe(cap, memory, request, size, output, capacity, length_output):
    """Read detached session metadata only; never pump packets, infer physical safety, restart a
    driver or replenish authority.

    The caller must belong to the capability's environment. The deployment must expose
    driver.describe and the grant must authorize driver.describe. Applicable grant purposes
    include driver.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the driver.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the checked zero-length request range.

    size (i64, unsigned bit pattern). Exact request length, 0 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `state` (`u64`), `sequence` (`u64`), `status` (`u64`), `effect_unknown` (`bool`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65552. The fixed result occupies 32 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('driver.describe', cap, memory, request, size, output, capacity, length_output)


def wr_driver_disconnect(cap, memory, request, size, output, capacity, length_output):
    """Release this connection and erase retained buffers. Best-effort release and local descriptor
    closure never terminate a shared driver. Independent receiver expiry remains mandatory.

    The caller must belong to the capability's environment. The deployment must expose
    driver.disconnect and the grant must authorize driver.disconnect. Applicable grant purposes
    include driver.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the driver.disconnect action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the checked zero-length request range.

    size (i64, unsigned bit pattern). Exact request length, 0 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `released` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65552. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('driver.disconnect', cap, memory, request, size, output, capacity, length_output)


def wr_driver_result(cap, memory, request, size, output, capacity, length_output):
    """Receive an exact sequence and incarnation-bound result. Failed guest delivery retains bytes.
    Timeout after send fences the session with effect_unknown; never retry a non-idempotent
    operation automatically.

    The caller must belong to the capability's environment. The deployment must expose
    driver.result and the grant must authorize driver.result. Applicable grant purposes include
    driver.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the driver.result action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `sequence` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `status` (`u64`), `payload` (`bytes`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65552. Reserve 16 bytes plus the route's configured maximum response payload even when
    the pending response is shorter.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. The response record contains the
    driver's status and payload."""
    return raw('driver.result', cap, memory, request, size, output, capacity, length_output)


def wr_driver_submit(cap, memory, request, size, output, capacity, length_output):
    """Submit one bounded fixed-contract request. Exact in-flight retry returns its receipt without
    resending. Changed bytes or deadline conflict; submission is local transport acceptance,
    never physical completion.

    The caller must belong to the capability's environment. The deployment must expose
    driver.submit and the grant must authorize driver.submit. Applicable grant purposes include
    driver.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the driver.submit action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `sequence` (`u64`), `deadline` (`u64`), `payload` (`bytes`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 65560 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `sequence` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65552. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('driver.submit', cap, memory, request, size, output, capacity, length_output)
