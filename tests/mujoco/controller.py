"""@brief Run the Go2 simulation through typed ROSv2 driver and steady-clock calls."""
import _struct
import wros

# The harness supplies the immutable wire template and the test case parameters.
def open_capability(alias):
    """@brief Require the exact capability approved for this simulation."""
    handle = wros.open(alias)
    assert not isinstance(handle, int)
    return handle


joint = open_capability("joint")
steady = open_capability("steady")
status, clock, size = wros.call("clock.create", steady, bytes(8), 8)
assert status == 0 and size == 8


def deadline():
    """@brief Get a command deadline from the deployment's steady clock domain."""
    status, sample, size = wros.call("clock.read", steady, clock, 32)
    assert status == 0 and size == 32
    return _struct.unpack_from("<Q", sample)[0] + 5_000_000_000


def poll(operation, payload):
    """@brief Wait for one bounded driver result without resubmitting a new action."""
    for _ in range(100_000):
        status, result, _size = wros.call(operation, joint, payload, 512)
        if status != 11:
            return status, result
    raise RuntimeError("driver response exceeded the polling budget")


assert poll("driver.connect", b"")[0] == 0
for sequence in range(1, steps + 1):
    request = bytearray(template)
    until = deadline()
    _struct.pack_into("<QQ", request, 0, sequence, until)
    _struct.pack_into("<Q", request, 32, sequence)
    _struct.pack_into("<Q", request, len(request) - 8, until)
    if mode == "success":
        target = 0.5 if sequence % 2 else -0.5
        _struct.pack_into("<d", request, target_offset, target)
    assert poll("driver.submit", bytes(request))[0] == 0
    status, result = poll("driver.result", _struct.pack("<Q", sequence))
    if mode == "crash":
        assert status in (5, 13)
        status, snapshot, size = wros.call("driver.describe", joint, b"", 512)
        assert status == 0 and size >= 32
        state, _, _, pending = _struct.unpack_from("<4Q", snapshot)
        assert state == 6 and pending == 1
    else:
        assert status == 0 and len(result) >= 24
        outcome, _, observed = _struct.unpack_from("<3Q", result)
        assert outcome == (0 if mode == "success" else 13) and observed == sequence

assert wros.call("driver.disconnect", joint, b"", 512)[0] == 0
