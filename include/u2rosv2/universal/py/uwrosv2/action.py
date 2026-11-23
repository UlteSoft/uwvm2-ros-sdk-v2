"""Raw action imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_action_cancel(cap, memory, request, size, output, capacity, length_output):
    """Cancellation proposal for owned goal; broader cancel set requires separate explicit scope.

    The caller must belong to the capability's environment. The deployment must expose
    action.cancel and the grant must authorize action.cancel. Applicable grant purposes include
    action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.cancel action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `client` (`u64`), `goal` (`u64`), `deadline` (`u64`).

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
    return raw('action.cancel', cap, memory, request, size, output, capacity, length_output)


def wr_action_cancel_set(cap, memory, request, size, output, capacity, length_output):
    """Separately authorized finite explicit cancellation of owned goals. Whole-set identity
    validation precedes native effects, each candidate has independent authority admission and
    outcome evidence, and exact retry never reissues a candidate. Unknown stops further
    attempts; no implicit wildcard or foreign-principal authority.

    The caller must belong to the capability's environment. The deployment must expose
    action.cancel.set and the grant must authorize action.cancel.set. Applicable grant purposes
    include action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.cancel.set action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `client` (`u64`), `selection` (`action_cancel_selection`), `deadline`
    (`u64`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`), `items` (`array<action_cancel_item>`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('action.cancel.set', cap, memory, request, size, output, capacity, length_output)


def wr_action_describe(cap, memory, request, size, output, capacity, length_output):
    """Sanitized endpoint/owned-goal state and retention; no unrelated UUID discovery.
    uwvm/action/State body follows action_endpoint_state.

    The caller must belong to the capability's environment. The deployment must expose
    action.describe and the grant must authorize action.describe. Applicable grant purposes
    include action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `endpoint` (`u64`), `goal` (`optional<u64>`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 4194304 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `state` (`message`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('action.describe', cap, memory, request, size, output, capacity, length_output)


def wr_action_open(cap, memory, request, size, output, capacity, length_output):
    """Fix action role, goal/feedback/result types and retention. Creation is asynchronous:
    explicit monotonically increasing key and finite absolute steady deadline; response is a
    request receipt, not an endpoint. communication.open.take retrieves a separately published
    typed handle.

    The caller must belong to the capability's environment. The deployment must expose
    action.open and the grant must authorize action.open. Applicable grant purposes include
    action. Depending on the selected inputs and plan, the VM also checks node.open,
    type.describe.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `endpoint` (`endpoint_request`), `creation_key` (`u64`), `deadline` (`u64`).

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
    return raw('action.open', cap, memory, request, size, output, capacity, length_output)


def wr_action_respond(cap, memory, request, size, output, capacity, length_output):
    """Legal transition and exact secondary action checked; accepted cancel is not terminal.

    The caller must belong to the capability's environment. The deployment must expose
    action.respond and the grant must authorize action.respond. Applicable grant purposes
    include action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.respond action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `endpoint` (`u64`), `response` (`action_response`), `deadline`
    (`u64`).

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
    return raw('action.respond', cap, memory, request, size, output, capacity, length_output)


def wr_action_submit(cap, memory, request, size, output, capacity, length_output):
    """Goal UUID is correlated with owned goal resource; not a transferable authority token.

    The caller must belong to the capability's environment. The deployment must expose
    action.submit and the grant must authorize action.submit. Applicable grant purposes include
    action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.submit action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `client` (`u64`), `goal` (`goal`), `deadline` (`u64`).

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
    return raw('action.submit', cap, memory, request, size, output, capacity, length_output)


def wr_action_take(cap, memory, request, size, output, capacity, length_output):
    """Goal proposal/status/feedback/result/cancel request are distinct closed event kinds.
    uwvm/action/Event body follows action_event; outer correlation is request, body goal/UUID
    remain distinct.

    The caller must belong to the capability's environment. The deployment must expose
    action.take and the grant must authorize action.take. Applicable grant purposes include
    action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the action.take action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `endpoint` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `record` (`delivery`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('action.take', cap, memory, request, size, output, capacity, length_output)
