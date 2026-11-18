module control;
import wros_scene : wros_abi;
extern(C) nothrow @nogc uint aggregate(const(uint)* values, size_t count)
{
    uint outValue = 0;
    foreach (i; 0 .. count) outValue += (i + 1) * values[i];
    return outValue;
}
extern(C) nothrow @nogc uint d_controller(uint selector)
{
    uint[4] values = [2, 4, 6, selector];
    return wros_abi() + aggregate(values.ptr, values.length);
}
