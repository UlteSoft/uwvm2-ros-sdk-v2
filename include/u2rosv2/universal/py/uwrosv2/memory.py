"""Pinned, guest-owned storage for raw WasmMTE-aware ROS calls."""
from _uwros_runtime import address as _address


class Buffer:
    """Own a contiguous writable byte span and retain its allocation while the view is live.

    Pass address to a raw ROS import and len(view) as its extent. Keep this object
    alive until the VM has completed every access to the range. A zero-capacity
    span still has an address. The VM reads lengths and handles as little-endian u64.
    """

    def __init__(self, data):
        """Allocate zeroed bytes for an integer size or copy the supplied bytes-like data."""
        self.view = memoryview(bytearray(data))

    @property
    def address(self):
        """Return the full tagged guest address of the first byte in this buffer."""
        return _address(self.view)

    def word(self, offset=0):
        """Read an unsigned little-endian 64-bit word from eight available bytes."""
        if offset < 0 or offset + 8 > len(self.view):
            raise ValueError("word exceeds the buffer")
        return int.from_bytes(self.view[offset:offset + 8], "little")

    def set_word(self, value, offset=0):
        """Write an unsigned little-endian 64-bit word into eight available bytes."""
        if offset < 0 or offset + 8 > len(self.view):
            raise ValueError("word exceeds the buffer")
        self.view[offset:offset + 8] = value.to_bytes(8, "little")
