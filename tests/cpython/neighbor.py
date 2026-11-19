"""@brief Inspect live CPython fixed and variable-size objects across allocation, release and reuse."""
import gc
import sys

shift = 56 if sys.maxsize > 2**32 else 28
mask = (1 << shift) - 1


def verify(make, extent):
    """@brief Require distinct colors on every observed pair within 64 bytes of the first object's end."""
    live = [make(i) for i in range(1024)]
    pairs = 0
    for epoch in range(8):
        # Both tested types have no GC prefix. Their Python-visible bodies are
        # conservative lower bounds for the physical extents allocated by libc.
        ordered = sorted((id(obj) & mask, id(obj) >> shift, extent(obj)) for obj in live)
        assert all(color for _, color, _ in ordered)
        for (left, left_color, size), (right, right_color, _) in zip(ordered, ordered[1:]):
            assert size > 0 and right - left >= size
            if right - left - size <= 64:
                assert left_color != right_color
                pairs += 1
        for i in range(epoch % 2, len(live), 2):
            live[i] = None
        gc.collect()
        for i, obj in enumerate(live):
            if obj is None:
                live[i] = make(i)
    assert pairs >= 512


verify(lambda i: object(), lambda obj: object.__basicsize__)
verify(lambda i: bytes((i & 255,)) * (128 + i % 3 * 16),
       lambda obj: bytes.__basicsize__ + len(obj) * bytes.__itemsize__)
