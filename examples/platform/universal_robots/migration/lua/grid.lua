--- @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates.
local function cell(width, x, y)
    return (y * width + x) & 0xffffffff
end
assert(cell(400,7,3)==1207 and cell(17,16,0)==16 and cell(9,0,5)==45)
