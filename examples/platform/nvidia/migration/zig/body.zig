//! Preserve the unsigned 32-bit row-major index of Noetic Costmap2D.
fn gridIndex(mx: u32, my: u32, width: u32) u32 {
    return my *% width +% mx;
}

export fn _start() void {
    const maximum: u32 = 0xffff_ffff;
    if (gridIndex(4, 7, 20) != 144 or gridIndex(9, maximum, 4) != 5 or
        gridIndex(0, maximum, maximum) != 1 or gridIndex(maximum, maximum, maximum) != 0) @trap();
}
