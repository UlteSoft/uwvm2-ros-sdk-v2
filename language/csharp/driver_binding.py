"""Lower a metadata-verified local driver connection check to bounded Wasm instructions."""
import re

from artifacts import sections, uleb
from scalar import checked_body


def field(data):
    return uleb(len(data)) + data


def section(code, data):
    return bytes((code,)) + field(data)


def constant(value):
    """@brief Encode the fixed nonnegative signed immediate of an integer instruction."""
    encoded = bytearray(uleb(value))
    if encoded[-1] & 0x40:
        encoded[-1] |= 0x80
        encoded.append(0)
    return bytes(encoded)


def signature(parameters, results):
    return b"\x60" + field(bytes(parameters)) + field(bytes(results))


def entry_body(alias_size):
    """@brief Open one alias, bound a connect attempt, clean up and call the managed policy.

    Only this wrapper can access its private memory. Handle, completion and
    output occupy disjoint, fixed eight-byte slots below the alias at byte 40.
    No address or length is supplied by managed guest code. The managed policy
    receives only the connect status. Cleanup failure and a denied operation
    that modified output trap after clearing all transient slots.
    """
    i32 = lambda value: b"\x41" + constant(value)
    i64 = lambda value: b"\x42" + constant(value)
    call = lambda index: b"\x10" + uleb(index)
    get = lambda index: b"\x20" + uleb(index)
    set_local = lambda index: b"\x21" + uleb(index)
    read = lambda offset: i32(offset) + b"\x29\x03\x00"  # i64.load
    save = lambda offset, value: i32(offset) + i64(value) + b"\x37\x03\x00"
    trap_if_nonzero = b"\x04\x40\x00\x0b"
    # Locals 0 = handle (i64), 1 = connect result (i32), 2 = cleanup/integrity error (i32).
    code = [b"\x02\x01\x7e\x02\x7f"]
    handle, reply, written = 8, 16, 24
    code += [i32(0), i64(40), i64(alias_size), i64(handle), call(0), trap_if_nonzero,
             read(handle), set_local(0), save(handle, 0),
             save(reply, 0x4321), save(written, 0x1234)]
    invoke = get(0) + i32(0) + i64(0) + i64(0) + i64(reply) + i64(8) + i64(written)
    code += [invoke, call(1), set_local(1),
             get(1), i32(13), b"\x46\x04\x40",  # if connect returned denied
             read(reply), i64(0x4321), b"\x52",  # i64.ne
             read(written), i64(0x1234), b"\x52\x72", set_local(2),  # i32.or
             b"\x05", invoke, call(2), set_local(2), b"\x0b",
             get(0), call(3), get(2), b"\x72", set_local(2),
             save(reply, 0), save(written, 0), get(2), trap_if_nonzero,
             get(1), call(4), trap_if_nonzero, b"\x0b"]
    return b"".join(code)


def driver_program(scalar, alias):
    """@brief Add an exact local connection binding to a proved register-only managed policy."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,62}", alias):
        raise ValueError("driver binding requires one literal ASCII alias of up to 63 bytes")
    encoded = alias.encode("ascii")
    i32, i64 = 0x7f, 0x7e
    types = [signature([i32, i64, i64, i64], [i32]), signature([i64, i32, *([i64] * 5)], [i32]),
             signature([i64], [i32]), signature([i32], [i32]), signature([], [])]
    imports = [(b"capability.open", 0), (b"driver.connect", 1), (b"driver.disconnect", 1), (b"capability.close", 2)]
    out = [scalar[:8], section(1, uleb(len(types)) + b"".join(types)), section(2, uleb(len(imports)) + b"".join(
        field(b"uwvm_ros_v2") + field(name) + b"\x00" + uleb(type_id) for name, type_id in imports)),
        section(3, b"\x02\x03\x04"), section(5, b"\x01\x01\x01\x01"),
        section(7, b"\x01" + field(b"_start") + b"\x00\x05")]
    for start, end, name, body in sections(scalar):
        kind = scalar[start]
        if kind == 10:
            out.append(section(10, b"\x02" + field(checked_body(body)) + field(entry_body(len(encoded)))))
            out.append(section(11, b"\x01\x00\x41\x28\x0b" + field(encoded)))
        elif kind == 0 and name != "name":
            out.append(scalar[start:end])
    names = [b"uwvm_ros_v2." + name for name, _ in imports] + [b"evaluate", b"_start"]
    out.append(section(0, field(b"name") + section(1, uleb(len(names)) + b"".join(
        uleb(index) + field(name) for index, name in enumerate(names)))))
    return b"".join(out)
