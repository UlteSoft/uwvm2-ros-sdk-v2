/** @file grid.ts
 * @brief Port the ROS Noetic Costmap2D row-major index to a core Wasm function.
 */

/** @brief Compute an index with the original unsigned 32-bit arithmetic. */
export function cellIndex(width: u32, x: u32, y: u32): u32 {
  return y * width + x;
}

/** @brief Verify row boundaries and unsigned arithmetic in the running guest. */
export function _start(): void {
  if (cellIndex(400, 7, 3) != 1207 ||
      cellIndex(17, 16, 0) != 16 ||
      cellIndex(17, 0, 1) != 17 ||
      cellIndex(u32.MAX_VALUE, 7, 2) != 5) unreachable();

  let state: u64 = 0x41c64e6d;
  for (let i: i32 = 0; i < 4096; ++i) {
    state = state * 6364136223846793005 + 1442695040888963407;
    const width = u32(state >> 32);
    const row = u32(state);
    const column = width > 0 ? row % width : 0;
    const expected = (u64(row) * u64(width) + u64(column)) & 0xffffffff;
    if (u64(cellIndex(width, column, row)) != expected) unreachable();
  }
}
