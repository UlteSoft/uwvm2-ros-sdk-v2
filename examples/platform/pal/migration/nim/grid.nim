## @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates.
proc cell(width, x, y: uint32): uint32 = y * width + x
doAssert cell(400,7,3) == 1207
doAssert cell(17,16,0) == 16
doAssert cell(9,0,5) == 45
