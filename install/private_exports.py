"""Restrict a compiler-produced Wasm32 component to its declared functions and one private memory."""
from artifacts import sections, uleb
from imports import inspect


def keep_private_memory(guest: bytes, expected_functions: set[str], *, max_pages: int = 65536) -> bytes:
    """Remove only LLD's conventional memory export, preserving other sections byte-for-byte.

    These component profiles require a single defined, bounded, unshared memory.
    Shared memories, imported memories and explicitly named exchange memories need
    their own ABI and cannot be hidden by this transformation.
    """
    if not expected_functions or "memory" in expected_functions or not 1 <= max_pages <= 65536:
        raise ValueError("invalid private memory profile")
    if any(row["kind"] == 2 for row in inspect(guest)):
        raise ValueError("the component must own its linear memory")
    result = [guest[:8]]
    memory_seen = False
    hidden = False
    exported = set()
    for start, end, _, body in sections(guest):
        kind = guest[start]
        if kind == 5:
            if memory_seen or body.count() != 1 or body.uint() != 1:
                raise ValueError("expected one bounded, unshared wasm32 memory")
            minimum, maximum = body.uint(), body.uint()
            if minimum > maximum or maximum > max_pages:
                raise ValueError("component memory range exceeds its profile")
            body.end()
            memory_seen = True
        if kind != 7:
            result.append(guest[start:end])
            continue
        entries = []
        for _ in range(body.count()):
            offset = body.position
            name, external_kind, index = body.name(), body.byte(), body.uint()
            if name == "memory" and external_kind == 2 and index == 0 and not hidden:
                hidden = True
                continue
            if name not in expected_functions or external_kind != 0 or name in exported:
                raise ValueError("unexpected component export: " + name)
            entries.append(bytes(body.data[offset:body.position]))
            exported.add(name)
        body.end()
        payload = uleb(len(entries)) + b"".join(entries)
        result.extend((b"\x07", uleb(len(payload)), payload))
    if not memory_seen or exported != expected_functions:
        raise ValueError("missing the component memory or declared function exports")
    return b"".join(result) if hidden else guest
