"""Raw replay imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_replay_open(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Replay uses an explicitly granted fixed source and exact object digests; it returns bytes
    only and never publishes or changes clocks.

    The caller must belong to the capability's environment. The deployment must expose
    replay.open and the grant must authorize replay.open. Applicable grant purposes include
    replay. Depending on the selected inputs and plan, the VM also checks resource.observe,
    data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the replay.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `source_capability` (`u64`), `profile` (`profile`), `objects` (`array<recording_object>`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 6072 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `replay` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('replay.open', cap, memory, request, size, output, capacity, length_output)


def wr_replay_read(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Replay uses an explicitly granted fixed source and exact object digests; it returns bytes
    only and never publishes or changes clocks.

    The caller must belong to the capability's environment. The deployment must expose
    replay.read and the grant must authorize replay.read. Applicable grant purposes include
    replay. Depending on the selected inputs and plan, the VM also checks resource.observe,
    data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the replay.read action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `replay` (`u64`), `limit` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `ordinal` (`u64`), `records` (`array<recording_message>`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('replay.read', cap, memory, request, size, output, capacity, length_output)


def wr_replay_seek(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Replay uses an explicitly granted fixed source and exact object digests; it returns bytes
    only and never publishes or changes clocks.

    The caller must belong to the capability's environment. The deployment must expose
    replay.seek and the grant must authorize replay.seek. Applicable grant purposes include
    replay. Depending on the selected inputs and plan, the VM also checks resource.observe,
    data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the replay.seek action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `replay` (`u64`), `ordinal` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `ordinal` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('replay.seek', cap, memory, request, size, output, capacity, length_output)
