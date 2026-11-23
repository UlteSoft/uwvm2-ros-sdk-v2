"""Raw timer imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_timer_cancel(cap, memory, request, size, output, capacity, length_output):
    """Disarm owned timer and notify waiters.

    The caller must belong to the capability's environment. The deployment must expose
    timer.cancel and the grant must authorize timer.cancel. Applicable grant purposes include
    timer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the timer.cancel action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `timer` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('timer.cancel', cap, memory, request, size, output, capacity, length_output)


def wr_timer_create(cap, memory, request, size, output, capacity, length_output):
    """Clock dependency needs independent read grant.

    The caller must belong to the capability's environment. The deployment must expose
    timer.create and the grant must authorize timer.create. Applicable grant purposes include
    timer. Depending on the selected inputs and plan, the VM also checks clock.read.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the timer.create action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `clock_capability` (`u64`), `clock` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `resource` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('timer.create', cap, memory, request, size, output, capacity, length_output)


def wr_timer_reset(cap, memory, request, size, output, capacity, length_output):
    """Overflow-checked schedule; zero period is one-shot.

    The caller must belong to the capability's environment. The deployment must expose
    timer.reset and the grant must authorize timer.reset. Applicable grant purposes include
    timer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the timer.reset action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `timer` (`u64`), `due` (`i64`), `period` (`i64`).

    size (i64, unsigned bit pattern). Exact request length, 24 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('timer.reset', cap, memory, request, size, output, capacity, length_output)


def wr_timer_take(cap, memory, request, size, output, capacity, length_output):
    """Coalesced occurrence record consumed only after delivery.

    The caller must belong to the capability's environment. The deployment must expose
    timer.take and the grant must authorize timer.take. Applicable grant purposes include timer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the timer.take action in the caller's
    environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `timer` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `expected` (`i64`), `actual` (`i64`), `occurrences` (`u64`), `clock_epoch` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 32 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('timer.take', cap, memory, request, size, output, capacity, length_output)
