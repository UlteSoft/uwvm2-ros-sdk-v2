# @brief Preserve Noetic Costmap2D's unsigned row-major index.
# The upstream method returns my * size_x_ + mx as an unsigned int.
def grid_index(mx, my, width)
  (my * width + mx) & 0xffffffff
end

raise "grid order" unless grid_index(4, 7, 20) == 144
raise "unsigned overflow" unless grid_index(9, 0xffffffff, 4) == 5
