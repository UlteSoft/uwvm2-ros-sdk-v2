// @file grid.odin
// @brief Port Noetic Costmap2D's unsigned row-major grid index.
package grid

@(export)
cell_index :: proc "c" (width, x, y: u32) -> u32 {
    return y * width + x
}

@(export, link_name="_start")
start :: proc "c" () {
    if cell_index(400, 7, 3) != 1207 ||
       cell_index(17, 16, 0) != 16 ||
       cell_index(17, 0, 1) != 17 ||
       cell_index(4294967295, 7, 2) != 5 {
        unreachable()
    }
}
