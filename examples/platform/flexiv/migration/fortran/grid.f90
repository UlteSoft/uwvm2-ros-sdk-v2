!> @brief Port the unsigned 32-bit index calculation in ROS Noetic Costmap2D.
program grid
  use iso_c_binding, only: c_int32_t, c_int64_t
  implicit none
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  if (cell(400,7,3) /= 1207 .or. cell(17,16,0) /= 16 .or. cell(9,0,5) /= 45) call abort_guest()
  if (cell(-1,1,1) /= 0 .or. cell(-1,-1,-1) /= 0) call abort_guest()
  if (cell(2147483647,1,1) /= int(z'80000000',c_int32_t)) call abort_guest()
contains
  !> @brief Compute (width * y + x) modulo 2**32 for arbitrary uint32 bit patterns.
  !! @param width Map width represented as a signed 32-bit bit pattern.
  !! @param x Column represented as a signed 32-bit bit pattern.
  !! @param y Row represented as a signed 32-bit bit pattern.
  !! @return The signed 32-bit representation of the original unsigned result.
  !! @details Sign extension preserves the low 32 bits. The signed 32-bit factors
  !! and addend fit in a 64-bit multiply-add, including the most negative input.
  pure integer(c_int32_t) function cell(width,x,y)
    integer(c_int32_t), intent(in) :: width,x,y
    integer(c_int64_t) :: value
    value = int(width,c_int64_t) * int(y,c_int64_t) + int(x,c_int64_t)
    value = iand(value, int(z'FFFFFFFF',c_int64_t))
    if (btest(value,31)) value = value - 4294967296_c_int64_t
    cell = int(value,c_int32_t)
  end function
end program
