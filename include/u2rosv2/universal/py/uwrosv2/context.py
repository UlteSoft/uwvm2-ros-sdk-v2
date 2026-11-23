"""Raw context imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_context_describe(cap, memory, request, size, output, capacity, length_output):
    """Sanitized context identity, supported features and shutdown state. Provider feature
    reporting distinguishes configured, native-attested supported and currently available
    states; missing/failed native feature probes are not affirmative support.

    The caller must belong to the capability's environment. The deployment must expose
    context.describe and the grant must authorize context.describe. Applicable grant purposes
    include context.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the context.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `context` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `profile` (`profile`), `state` (`text`), `generation` (`u64`), `features`
    (`array<provider_feature>`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('context.describe', cap, memory, request, size, output, capacity, length_output)


def wr_context_open(cap, memory, request, size, output, capacity, length_output):
    """Create an independently owned context only after complete provider/security closure
    validation.

    The caller must belong to the capability's environment. The deployment must expose
    context.open and the grant must authorize context.open. Applicable grant purposes include
    context.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the context.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `profile` (`profile`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('context.open', cap, memory, request, size, output, capacity, length_output)


def wr_context_shutdown(cap, memory, request, size, output, capacity, length_output):
    """Cancel owned work and wake waits; never process exit.

    The caller must belong to the capability's environment. The deployment must expose
    context.shutdown and the grant must authorize context.shutdown. Applicable grant purposes
    include context.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the context.shutdown action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `context` (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('context.shutdown', cap, memory, request, size, output, capacity, length_output)
