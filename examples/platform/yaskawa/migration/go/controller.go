// @brief Row-major indexing for a ROS Noetic costmap_2d grid.
package robot

// @brief Compute the index as Costmap2D::getIndex does in ros-planning/navigation.
// @param mx Grid column. @param my Grid row. @param width Columns per row.
// @return The uint32 row-major index. The caller validates grid extents.
func CellIndex(mx, my, width uint32) uint32 { return my*width + mx }

// @brief Check an interior cell, a row boundary and unsigned wraparound.
// @return Zero when all results match the source algorithm.
func Start() uint32 {
    return (CellIndex(3, 2, 10) ^ 23) | (CellIndex(0, 1, 8) ^ 8) | (CellIndex(1, 1, 0xffffffff) ^ 0)
}
