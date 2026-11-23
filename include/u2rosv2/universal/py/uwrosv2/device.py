"""Raw device imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_device_describe(cap, memory, request, size, output, capacity, length_output):
    """Actual provider/firmware support, state and watchdog contract.

    The caller must belong to the capability's environment. The deployment must expose
    device.describe and the grant must authorize device.describe. Applicable grant purposes
    include device.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the device.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `device` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `description` (`device_description`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4096.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('device.describe', cap, memory, request, size, output, capacity, length_output)


def wr_device_open(cap, memory, request, size, output, capacity, length_output):
    """Approved bus/protocol/command envelope, independent watchdog and finite capacity.

    The caller must belong to the capability's environment. The deployment must expose
    device.open and the grant must authorize device.open. Applicable grant purposes include
    device.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the device.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `profile` (`profile`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 16384 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4096. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('device.open', cap, memory, request, size, output, capacity, length_output)


def wr_device_result(cap, memory, request, size, output, capacity, length_output):
    """Distinguish accepted, observed execution, partial and unknown effect.

    The caller must belong to the capability's environment. The deployment must expose
    device.result and the grant must authorize device.result. Applicable grant purposes include
    device.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the device.result action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `device` (`u64`), `request` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`), `evidence` (`optional<execution_evidence>`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4096.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('device.result', cap, memory, request, size, output, capacity, length_output)


def wr_device_stop(cap, memory, request, size, output, capacity, length_output):
    """Requires explicit stop authority; trusted watchdog independent.

    The caller must belong to the capability's environment. The deployment must expose
    device.stop and the grant must authorize device.stop. Applicable grant purposes include
    device.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the device.stop action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`request_key`), `device` (`u64`), `profile` (`profile`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 16384 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4096.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('device.stop', cap, memory, request, size, output, capacity, length_output)


def wr_device_submit(cap, memory, request, size, output, capacity, length_output):
    """Full command bounds/freshness/units/frame before hardware effect.

    The caller must belong to the capability's environment. The deployment must expose
    device.submit and the grant must authorize device.submit. Applicable grant purposes include
    device. Depending on the selected inputs and plan, the VM also checks device.stop,
    control.submit, resource.observe, buffer.read, data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the device.submit action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `command` (`command`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 16384 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `receipt` (`receipt`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4096.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available. Inspect the delivered receipt for
    the operation's outcome."""
    return raw('device.submit', cap, memory, request, size, output, capacity, length_output)
