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
    raw = section.take(section.uint())
    body = Reader(raw)
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
    return raw


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


def scene_program(scalar):
    """Lower the validated Abi() and Policy(int) calls to a private Wasm entry.

    In the resulting function index space, 0 is the ABI import, 1 is the
    unmodified compiled policy and 2 is startup. The first code body's offset
    in the code section stays stable for the policy's DWARF line information.
    """
    from artifacts import uleb

    def field(data):
        return uleb(len(data)) + data

    def section(kind, data):
        return bytes([kind]) + field(data)

    module, operation = b"uwvm_ros_v2", b"abi"
    entry = bytes.fromhex("00 10 00 10 01 04 40 00 0b 0b")  # if (Policy(Abi())) trap
    function_types = bytes.fromhex("03 60 01 7f 01 7f 60 00 01 7f 60 00 00")
    function_names = b"\x03" + b"".join(bytes([i]) + field(name) for i, name in
                                         enumerate((module + b"." + operation, b"evaluate", b"_start")))
    out = [scalar[:8]]
    for start, end, name, body in sections(scalar):
        kind = scalar[start]
        if kind == 1:
            out.append(section(1, function_types))
            out.append(section(2, b"\x01" + field(module) + field(operation) + b"\x00\x01"))
        elif kind == 3:
            out.append(section(3, b"\x02\x00\x02"))
        elif kind == 7:
            out.append(section(7, b"\x01" + field(b"_start") + b"\x00\x02"))
        elif kind == 10:
            policy = checked_body(body)
            out.append(section(10, b"\x02" + field(policy) + field(entry)))
        elif not kind and name != "name":
            out.append(scalar[start:end])
        elif kind:
            raise ValueError("unexpected state in C# scene policy")
    out.append(section(0, field(b"name") + section(1, function_names)))
    return b"".join(out)
