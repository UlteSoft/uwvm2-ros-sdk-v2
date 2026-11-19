"""@brief Inspect colored live guest CPython objects across repeated allocation and destruction."""
import gc
import sys

shift = 56 if sys.maxsize > 2**32 else 28
mask = (1 << shift) - 1
live = [object() for _ in range(256)]
pairs = 0
for round_index in range(8):
    tagged = sorted((id(obj) & mask, id(obj) >> shift) for obj in live)
    for (left, left_color), (right, right_color) in zip(tagged, tagged[1:]):
        if right - left <= 64:
            assert left_color and right_color and left_color != right_color
            pairs += 1
    for n in range(round_index % 2, len(live), 2):
        live[n] = None
    gc.collect()
    for n, obj in enumerate(live):
        if obj is None:
            live[n] = object()
assert pairs >= 512
