"""Raw buffer imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_buffer_create(cap, memory, request, size, output, capacity, length_output):
    """Reserve bounded data/workspace before publication.

    The caller must belong to the capability's environment. The deployment must expose
    buffer.create and the grant must authorize buffer.create. Applicable grant purposes include
    buffer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the buffer.create action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `layout` (`buffer_layout`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194328 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194816. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('buffer.create', cap, memory, request, size, output, capacity, length_output)


def wr_buffer_describe(cap, memory, request, size, output, capacity, length_output):
    """Untrusted origin cannot be relabelled as a trusted sensor.

    The caller must belong to the capability's environment. The deployment must expose
    buffer.describe and the grant must authorize buffer.describe. Applicable grant purposes
    include buffer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the buffer.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `buffer` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `layout` (`buffer_layout`), `sealed` (`bool`), `provenance` (`text`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194816.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('buffer.describe', cap, memory, request, size, output, capacity, length_output)


def wr_buffer_read(cap, memory, request, size, output, capacity, length_output):
    """Exact bounded read; no host descriptor export.

    The caller must belong to the capability's environment. The deployment must expose
    buffer.read and the grant must authorize buffer.read. Applicable grant purposes include
    buffer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the buffer.read action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `buffer` (`u64`), `offset` (`u64`), `bytes` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 24 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `data` (`bytes`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194816.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('buffer.read', cap, memory, request, size, output, capacity, length_output)


def wr_buffer_seal(cap, memory, request, size, output, capacity, length_output):
    """Immutable publication with digest and registered layout.

    The caller must belong to the capability's environment. The deployment must expose
    buffer.seal and the grant must authorize buffer.seal. Applicable grant purposes include
    buffer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the buffer.seal action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `buffer` (`u64`), `digest` (`bytes`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194328 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `reference` (`buffer_ref`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194816. The fixed result occupies 16 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('buffer.seal', cap, memory, request, size, output, capacity, length_output)


def wr_buffer_write(cap, memory, request, size, output, capacity, length_output):
    """Contiguous bounded write only before seal; no native pointer.

    The caller must belong to the capability's environment. The deployment must expose
    buffer.write and the grant must authorize buffer.write. Applicable grant purposes include
    buffer.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the buffer.write action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `buffer` (`u64`), `expected_offset` (`u64`), `data` (`bytes`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194328 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `accepted_bytes` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194816. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('buffer.write', cap, memory, request, size, output, capacity, length_output)
