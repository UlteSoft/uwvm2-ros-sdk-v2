"""Raw recording imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_recording_append(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
    checkpoint. Checkpoint is complete volatile acceptance, not durable storage.

    The caller must belong to the capability's environment. The deployment must expose
    recording.append and the grant must authorize recording.append. Applicable grant purposes
    include recording. Depending on the selected inputs and plan, the VM also checks
    buffer.read, data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the recording.append action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `writer` (`u64`), `key` (`u64`), `items` (`array<recording_buffer_item>`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 6072 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`recording_receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 104 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('recording.append', cap, memory, request, size, output, capacity, length_output)


def wr_recording_checkpoint(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
    checkpoint. Checkpoint is complete volatile acceptance, not durable storage.

    The caller must belong to the capability's environment. The deployment must expose
    recording.checkpoint and the grant must authorize recording.checkpoint. Applicable grant
    purposes include recording.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the recording.checkpoint action in
    the caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `writer` (`u64`), `key` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`recording_receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 104 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('recording.checkpoint', cap, memory, request, size, output, capacity, length_output)


def wr_recording_open(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
    checkpoint. Checkpoint is complete volatile acceptance, not durable storage.

    The caller must belong to the capability's environment. The deployment must expose
    recording.open and the grant must authorize recording.open. Applicable grant purposes
    include recording.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the recording.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `profile` (`profile`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 6072 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `writer` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('recording.open', cap, memory, request, size, output, capacity, length_output)


def wr_recording_stop(cap, memory, request, size, output, capacity, length_output):
    """Private finite volatile MCAP store with exact deployment channel/buffer profiles, caller
    incarnation ownership, atomic source read/export authority and retained pinned objects.
    Writer mutations use next-key exact recovery; resource.close releases writer or an unpinned
    checkpoint. Checkpoint is complete volatile acceptance, not durable storage.

    The caller must belong to the capability's environment. The deployment must expose
    recording.stop and the grant must authorize recording.stop. Applicable grant purposes
    include recording.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the recording.stop action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `writer` (`u64`), `key` (`u64`), `drain` (`bool`).

    size (i64, unsigned bit pattern). Exact request length, 24 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`recording_receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 104 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('recording.stop', cap, memory, request, size, output, capacity, length_output)
