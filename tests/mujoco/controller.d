import wros_scene : wros_capability_open, wros_driver_connect, wros_driver_submit,
                    wros_driver_result, wros_driver_describe, wros_driver_disconnect;

__gshared ulong joint, used, sequence;
__gshared ulong[64] response;
__gshared ubyte[5] nameBytes = [106, 111, 105, 110, 116];

private ulong address(const(void)* data) nothrow @nogc
{
    return cast(ulong)cast(size_t)data;
}

private uint invoke(alias operation)(const(void)* input, size_t length) nothrow @nogc
{
    return operation(joint, 0, address(input), length, address(response.ptr),
                     response.sizeof, address(&used));
}

private uint poll(alias operation)(const(void)* input, size_t length) nothrow @nogc
{
    foreach (attempt; 0 .. 10_000_000)
    {
        const result = invoke!operation(input, length);
        if (result != 11) return result;
    }
    return 11;
}

private void put64(size_t offset, ulong value) nothrow @nogc
{
    foreach (i; 0 .. 8)
        request[offset + i] = cast(ubyte)(value >> (i * 8));
}

extern(C) uint wros_main() nothrow @nogc
{
    if (wros_capability_open(0, address(nameBytes.ptr), nameBytes.length, address(&joint)) != 0)
        return 1;
    if (poll!wros_driver_connect(null, 0) != 0) return 2;

    for (sequence = 1; sequence <= steps; ++sequence)
    {
        put64(0, sequence);
        put64(32, sequence);
        static if (success)
            put64(targetOffset, sequence % 2 ? 0x3fe0000000000000UL : 0xbfe0000000000000UL);

        if (poll!wros_driver_submit(request.ptr, request.length) != 0) return 3;
        const status = poll!wros_driver_result(&sequence, sequence.sizeof);
        static if (crash)
        {
            if (status != 5 && status != 13) return 4;
            if (invoke!wros_driver_describe(null, 0) != 0) return 5;
            if (used < 32 || response[0] != 6 || response[3] != 1) return 6;
        }
        else
        {
            if (status != 0 || used < 24 || response[0] != (success ? 0 : 13) || response[2] != sequence)
                return 7;
        }
    }
    return invoke!wros_driver_disconnect(null, 0);
}
