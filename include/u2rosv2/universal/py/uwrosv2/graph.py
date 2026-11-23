"""Raw graph imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_graph_snapshot(cap, memory, request, size, output, capacity, length_output):
    """Exact filtered discovery through an explicitly owned observer node and context; observer
    node profile and actual parent context must match, with counted attachment capacity and
    complete origin authority.

    The caller must belong to the capability's environment. The deployment must expose
    graph.snapshot and the grant must authorize graph.snapshot. Applicable grant purposes
    include discovery. Depending on the selected inputs and plan, the VM also checks
    context.describe, node.open, context.open.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the graph.snapshot action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `context_capability` (`u64`), `context` (`u64`), `observer_node_capability` (`u64`),
    `observer_node` (`u64`), `profile` (`profile`), `cursor` (`optional<u64>`), `limit` (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`page`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('graph.snapshot', cap, memory, request, size, output, capacity, length_output)


def wr_graph_watch(cap, memory, request, size, output, capacity, length_output):
    """Exact filtered discovery through an explicitly owned observer node and context; observer
    node profile and actual parent context must match, with counted attachment capacity and
    complete origin authority.

    The caller must belong to the capability's environment. The deployment must expose
    graph.watch and the grant must authorize graph.watch. Applicable grant purposes include
    discovery. Depending on the selected inputs and plan, the VM also checks context.describe,
    node.open, context.open.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the graph.watch action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `context_capability` (`u64`), `context` (`u64`), `observer_node_capability` (`u64`),
    `observer_node` (`u64`), `profile` (`profile`).

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
    return raw('graph.watch', cap, memory, request, size, output, capacity, length_output)
