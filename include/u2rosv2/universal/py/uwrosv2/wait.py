"""Raw wait imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_wait_acknowledge(cap, memory, request, size, output, capacity, length_output):
    """Acknowledge source sequence; readiness is not data consumption.

    The caller must belong to the capability's environment. The deployment must expose
    wait.acknowledge and the grant must authorize wait.acknowledge. Applicable grant purposes
    include wait.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the wait.acknowledge action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `waitset` (`u64`), `source` (`u64`), `sequence` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 24 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('wait.acknowledge', cap, memory, request, size, output, capacity, length_output)


def wr_wait_add(cap, memory, request, size, output, capacity, length_output):
    """Source requires independent resource.observe; bounded membership.

    The caller must belong to the capability's environment. The deployment must expose wait.add
    and the grant must authorize wait.add. Applicable grant purposes include wait. Depending on
    the selected inputs and plan, the VM also checks resource.observe.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the wait.add action in the caller's
    environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `waitset` (`u64`), `source_capability` (`u64`), `source` (`u64`), `interests` (`u64`),
    `token` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 40 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('wait.add', cap, memory, request, size, output, capacity, length_output)


def wr_wait_create(cap, memory, request, size, output, capacity, length_output):
    """Create empty owned waitset.

    The caller must belong to the capability's environment. The deployment must expose
    wait.create and the grant must authorize wait.create. Applicable grant purposes include
    wait.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the wait.create action in the
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
    return raw('wait.create', cap, memory, request, size, output, capacity, length_output)


def wr_wait_poll(cap, memory, request, size, output, capacity, length_output):
    """Nonconsuming bounded readiness; infinite wait explicit; authority revalidated after wake.

    The caller must belong to the capability's environment. The deployment must expose wait.poll
    and the grant must authorize wait.poll. Applicable grant purposes include wait.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the wait.poll action in the caller's
    environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `waitset` (`u64`), `duration_ns` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `records` (`array<ready_record>`). Each 32-byte record contains source, token, events and
    sequence, with no array length prefix.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('wait.poll', cap, memory, request, size, output, capacity, length_output)


def wr_wait_remove(cap, memory, request, size, output, capacity, length_output):
    """Detach exact source from owned waitset.

    The caller must belong to the capability's environment. The deployment must expose
    wait.remove and the grant must authorize wait.remove. Applicable grant purposes include
    wait.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the wait.remove action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `waitset` (`u64`), `source` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the checked reply range. This operation
    has an empty reply body.

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 0 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. The VM writes a
    zero length before the mutation. A later refusal can therefore also leave zero in the slot."""
    return raw('wait.remove', cap, memory, request, size, output, capacity, length_output)
