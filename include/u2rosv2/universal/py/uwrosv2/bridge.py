"""Raw bridge imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_bridge_create(cap, memory, request, size, output, capacity, length_output):
    """Both endpoint directions/types/conversion/QoS preflight independently.

    The caller must belong to the capability's environment. The deployment must expose
    bridge.create and the grant must authorize bridge.create. Applicable grant purposes include
    bridge. Depending on the selected inputs and plan, the VM also checks topic.reserve,
    topic.acknowledge, topic.release, topic.describe, data.export, topic.publish.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the bridge.create action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `bridge` (`bridge_request`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4096 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 1024. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('bridge.create', cap, memory, request, size, output, capacity, length_output)


def wr_bridge_describe(cap, memory, request, size, output, capacity, length_output):
    """Conversion/loss/QoS degradation/loop/correlation state only within scope.

    The caller must belong to the capability's environment. The deployment must expose
    bridge.describe and the grant must authorize bridge.describe. Applicable grant purposes
    include bridge.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the bridge.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `bridge` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `description` (`bridge_description`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 1024.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('bridge.describe', cap, memory, request, size, output, capacity, length_output)


def wr_bridge_start(cap, memory, request, size, output, capacity, length_output):
    """Revalidate both grants and generation; no unchecked forwarding thread.

    The caller must belong to the capability's environment. The deployment must expose
    bridge.start and the grant must authorize bridge.start. Applicable grant purposes include
    bridge. Depending on the selected inputs and plan, the VM also checks topic.reserve,
    topic.acknowledge, topic.release, topic.describe, data.export, topic.publish.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the bridge.start action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `bridge` (`u64`), `deadline` (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4096 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 1024.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('bridge.start', cap, memory, request, size, output, capacity, length_output)


def wr_bridge_stop(cap, memory, request, size, output, capacity, length_output):
    """Stop admitted direction, drain/cancel declared in profile.

    The caller must belong to the capability's environment. The deployment must expose
    bridge.stop and the grant must authorize bridge.stop. Applicable grant purposes include
    bridge.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the bridge.stop action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `bridge` (`u64`), `profile` (`profile`), `deadline` (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4096 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 1024.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('bridge.stop', cap, memory, request, size, output, capacity, length_output)
