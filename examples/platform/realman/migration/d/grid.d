/** @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates. */
module application;
uint cell(uint width, uint x, uint y) nothrow @nogc { return y * width + x; }
extern(C) uint wros_main() nothrow @nogc {
    return cell(400,7,3)==1207 && cell(17,16,0)==16 && cell(9,0,5)==45 ? 0 : 1;
}
