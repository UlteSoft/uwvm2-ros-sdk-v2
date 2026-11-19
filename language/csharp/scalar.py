"""Admit register-only C# kernels at the final core-Wasm instruction boundary."""
from artifacts import sections
from imports import Reader


def checked_body(section):
    """Consume the one integer function, including immediates and local types.

    Reject unknown opcodes, calls, pointer inspection and linear-memory access.
    Structured control and local indices remain subject to full VM validation.
    """
    if section.count() != 1:
        raise ValueError("expected one C# scalar body")
    body = Reader(section.take(section.uint()))
    section.end()
    for _ in range(body.count()):
        body.uint()
        if body.byte() not in (0x7e, 0x7f):
            raise ValueError("non-integer local in C# scalar kernel")
    depth = 1
    while depth:
        op = body.byte()
        if op in (0x02, 0x03, 0x04):  # block, loop, if
            if body.byte() not in (0x40, 0x7e, 0x7f):
                raise ValueError("non-scalar block signature")
            depth += 1
        elif op == 0x0b:
            depth -= 1
        elif op in (0x0c, 0x0d, 0x20, 0x21, 0x22):  # branches, local.get/set/tee
            body.uint()
        elif op == 0x0e:  # br_table, including the default destination
            for _ in range(body.count() + 1):
                body.uint()
        elif op in (0x41, 0x42):
            body.sint(32 if op == 0x41 else 64)
        elif (op in (0x00, 0x01, 0x05, 0x0f, 0x1a, 0x1b, 0xa7, 0xac, 0xad)
              or 0x45 <= op <= 0x5a or 0x67 <= op <= 0x8a or 0xc0 <= op <= 0xc4):
            continue
        else:
            raise ValueError(f"C# scalar proof rejects opcode 0x{op:02x}")
    body.end()


def prove_scalar(guest):
    """Return a module with no memories and exactly one closed integer function.

    The linker emits a private bounded memory even for register-only leaves.
    Admit its exact shape before removal. Preserve function indices and debug
    sections. No executable payload is synthesized or changed by this pass.
    """
    expected = {
        1: bytes.fromhex("01 60 01 7f 01 7f"),  # (i32) -> i32
        3: bytes.fromhex("01 00"),                # evaluate, type 0
        5: bytes.fromhex("01 01 01 01"),          # 1..1, not shared
        7: b"\x01\x08evaluate\x00\x00",
    }
    seen = []
    out = [guest[:8]]
    for start, end, _, body in sections(guest):
        kind = guest[start]
        if kind:
            seen.append(kind)
            if kind == 10:
                checked_body(body)
            elif kind not in expected or body.data != expected[kind]:
                raise ValueError(f"C# scalar proof rejects section {kind}")
        if kind != 5:
            out.append(guest[start:end])
    if seen != [1, 3, 5, 7, 10]:
        raise ValueError("C# scalar proof requires exactly one closed integer method")
    return b"".join(out)
