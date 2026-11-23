"""Raw capability imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_abi():
    """Returns major 2 only when explicitly exposed; errors encoded in same i32 result.

    The deployment must expose abi to the immediate caller.

    Call from the guest bound to this import. This signature has no guest memory operands.

    Returns an i32 as a Python int. The major ABI number (2) on success. The same i32 carries a
    scene status on failure."""
    return raw('abi')


def wr_capability_close(id):
    """Close capability handle without resetting budgets or resource lifetime.

    The caller must be an enrolled member of the handle's environment with capability.close
    exposed.

    Call from the guest bound to this import. This signature has no guest memory operands.

    id (i64, unsigned bit pattern). Handle issued by capability.open in the caller's
    environment.

    Returns an i32 as a Python int. Zero retires the handle. BAD_HANDLE (9) identifies an
    unknown or already closed handle in the authorized environment."""
    return raw('capability.close', id)


def wr_capability_open(memory, offset, size, output):
    """Exact existing alias; no grant creation or upgrade; undelivered handle rolled back.

    The caller must belong to an environment that exposes capability.open and grants the exact,
    live alias.

    Keep the alias readable and the handle slot writable through the call. Their ranges may
    overlap. The VM copies the alias before writing the handle. Preserve WasmMTE tags on both
    addresses.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing both
    spans.

    offset (i64, unsigned bit pattern). Guest address of the raw ASCII grant alias. Letters,
    digits, underscore, hyphen and period are allowed. The exact names `.` and `..` are invalid.

    size (i64, unsigned bit pattern). Alias length from 1 through 255 bytes, excluding any
    terminator or wire prefix.

    output (i64, unsigned bit pattern). Guest address of the writable eight-byte little-endian
    handle slot.

    Returns an i32 as a Python int. Zero after writing the handle. Invalid alias bytes, invalid
    memory or failed handle delivery return INVALID (22). Failed delivery rolls back the
    unpublished handle. An absent or revoked alias returns DENIED (13)."""
    return raw('capability.open', memory, offset, size, output)


def wr_capability_revoke(cap, memory, request, size, output, capacity, length_output):
    """Permanently revoke exactly the carrier capability grant. The target must equal the carrier
    capability, the exact grant must contain capability.revoke and the import must be exposed.
    One pre-reserved receipt per grant retains the nonzero retry key, exact caller incarnation
    and target. Atomically fence admissions before nonblocking provider retirement
    notifications. Retirement state 1 means fenced with notification pending; 2 means local
    notifications returned, never proof of native process exit, remote cancellation or physical
    stop. Exact retry can recover failed output after revocation without repeating notifications
    or allocating. Closing the handle or retiring the caller removes recovery access. No traffic
    quota may prevent this independently authorized authority reduction; short output and
    cancellation reject before fencing. Reopening cannot restore the grant; only trusted
    deployment creates new authority.

    The caller must belong to the capability's environment. The deployment must expose
    capability.revoke and the grant must authorize capability.revoke.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may
    overlap because the VM copies the request before delivery. The length slot must be disjoint
    from both ranges after address normalization. An overlap with the slot returns INVALID (22).

    cap (i64, unsigned bit pattern). Capability handle for the capability.revoke action in the
    caller's environment.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `key` (`u64`), `target_capability` (`u64`).

    size (i64, unsigned bit pattern). Exact request length, 16 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `key` (`u64`), `target_capability` (`u64`), `revocation_identity` (`u64`),
    `retirement_state` (`u64`).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 4194304. The fixed result occupies 32 bytes.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero on success, otherwise a scene status. A short reply
    returns TOO_LARGE (90) with the required capacity or minimum in the length slot. Other
    limits may return 90 before a useful size is available."""
    return raw('capability.revoke', cap, memory, request, size, output, capacity, length_output)
