"""Raw node imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_node_describe(cap, memory, request, size, output, capacity, length_output):
    """Only owned resolved identity and enabled features.

    The caller must belong to the capability's environment. The deployment must expose
    node.describe and the grant must authorize node.describe. Applicable grant purposes include
    node.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the node.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `node` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `name` (`text`), `namespace` (`text`), `profile` (`profile`), `generation` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('node.describe', cap, memory, request, size, output, capacity, length_output)


def wr_node_open(cap, memory, request, size, output, capacity, length_output):
    """Resolve immutable node/name/remapping/profile under exact parent context grant. Creation is
    asynchronous: explicit monotonically increasing key and finite absolute steady deadline;
    response is a request receipt, not an endpoint. communication.open.take retrieves a
    separately published typed handle.

    The caller must belong to the capability's environment. The deployment must expose node.open
    and the grant must authorize node.open. Applicable grant purposes include node. Depending on
    the selected inputs and plan, the VM also checks context.open.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the node.open action in the caller's
    environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `context_capability` (`u64`), `context` (`u64`), `profile` (`profile`), `creation_key`
    (`u64`), `deadline` (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `creation` (`communication_creation_receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 48 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('node.open', cap, memory, request, size, output, capacity, length_output)
