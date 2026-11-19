!> @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates.
program grid
  use iso_c_binding, only: c_int32_t
  implicit none
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  if(cell(400,7,3) /= 1207 .or. cell(17,16,0) /= 16 .or. cell(9,0,5) /= 45) call abort_guest()
contains
  pure integer(c_int32_t) function cell(width,x,y)
    integer(c_int32_t), intent(in) :: width,x,y
    cell=width*y+x
  end function
end program
