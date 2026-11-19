# @brief Preserve Noetic Costmap2D's unsigned row-major index.
# The upstream method returns my * size_x_ + mx as an unsigned int.
def grid_index(mx, my, width)
  # Form the low 32 bits without overflowing mruby's signed 64-bit Integer.
  half = (1 << 16) - 1
  low = (my & half) * (width & half)
  high = ((my >> 16) * (width & half) + (width >> 16) * (my & half)) & half
  (low + (high << 16) + mx) & ((1 << 32) - 1)
end

maximum = (1 << 32) - 1
raise "grid order" unless grid_index(4, 7, 20) == 144
raise "linear wrap" unless grid_index(9, maximum, 4) == 5
raise "wide product wrap" unless grid_index(0, maximum, maximum) == 1
raise "wide addition wrap" unless grid_index(maximum, maximum, maximum) == 0
