"""Raw sensor imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_sensor_describe(cap, memory, request, size, output, capacity, length_output):
    """Bound source identity, loss and negotiated capabilities; no credentials.

    The caller must belong to the capability's environment. The deployment must expose
    sensor.describe and the grant must authorize sensor.describe. Applicable grant purposes
    include sensor.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the sensor.describe action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `sensor` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `profile` (`profile`), `state` (`message`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4196352.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('sensor.describe', cap, memory, request, size, output, capacity, length_output)


def wr_sensor_open(cap, memory, request, size, output, capacity, length_output):
    """Ingress-only approved source/transport/schema/queue; no send/listen authority.

    The caller must belong to the capability's environment. The deployment must expose
    sensor.open and the grant must authorize sensor.open. Applicable grant purposes include
    sensor.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the sensor.open action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `profile` (`profile`).

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 144 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `handle` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4196352. The fixed result occupies 8 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('sensor.open', cap, memory, request, size, output, capacity, length_output)


def wr_sensor_take(cap, memory, request, size, output, capacity, length_output):
    """Validated complete frame with timestamp origin and discontinuity. Capacity for the largest
    complete frame is checked before native read. The local capture ordinal and optional actual
    native sequence are distinct. Failed guest copy retains the frame for retry.

    The caller must belong to the capability's environment. The deployment must expose
    sensor.take and the grant must authorize sensor.take. Applicable grant purposes include
    sensor. Depending on the selected inputs and plan, the VM also checks data.export.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the sensor.take action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `sensor` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 8 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `record` (`delivery`), `buffer` (`u64`), `schema` (`profile`), `buffer_profile` (`profile`),
    `frame` (`text`), `units` (`text`), `source` (`u64`), `native_sequence` (`optional<u64>`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4196352.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('sensor.take', cap, memory, request, size, output, capacity, length_output)
