"""@brief Verify the platform child and the parent driver grant each fence an unapproved handshake."""
import wros

arm = wros.open("arm")
assert not isinstance(arm, int), ("missing parent capability", arm)
status, payload, written = wros.call("driver.connect", arm, b"", 8)
assert (status, payload, written) == (13, None, 0), (status, written)
assert wros.close(arm) == 0
