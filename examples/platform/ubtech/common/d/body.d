/** @brief Check the ROSv2 ABI inside the guest and fail on mismatch. */
module application;

import wros_scene : wros_abi;

extern(C) nothrow @nogc uint weighted(const(uint)* values, size_t count)
{
    uint total;
    foreach (index; 0 .. count)
        total += (index + 1) * values[index];
    return total;
}

extern(C) nothrow @nogc uint wros_main()
{
    uint[4] samples = [2, 4, 6, wros_abi() + 3];
    return weighted(samples.ptr, samples.length) == 48 ? 0 : 1;
}
