/** @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates. */
static unsigned cell(unsigned width, unsigned x, unsigned y) {
    return y * width + x;
}
extern "C" void _start(void) {
    if (cell(400, 7, 3) != 1207 || cell(17, 16, 0) != 16 || cell(9, 0, 5) != 45) __builtin_trap();
}
