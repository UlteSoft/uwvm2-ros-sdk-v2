!> @brief Verify an isolated driver's parent grant and platform-specific child policy.
program driver_check
  use iso_c_binding
  use wros_scene, only: wr_capability_open, wr_capability_close, wr_driver_connect
  implicit none
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  character(kind=c_char), target :: name(3) = ['a','r','m']
  integer(c_int64_t), target :: handle=0, output=17185, written=4660
  integer(c_int32_t) :: status
  status=wr_capability_open(0_c_int32_t, address(c_loc(name)), 3_c_int64_t, address(c_loc(handle)))
  if (status /= 0) call abort_guest()
  status=wr_driver_connect(handle,0_c_int32_t,0_c_int64_t,0_c_int64_t,address(c_loc(output)),8_c_int64_t,address(c_loc(written)))
  if (status /= 13 .or. output /= 17185 .or. written /= 4660) call abort_guest()
  if (wr_capability_close(handle) /= 0) call abort_guest()
contains
  !> @brief Preserve all 32 address bits in the ROSv2 address operand.
  integer(c_int64_t) function address(p)
    type(c_ptr), value :: p
    address=iand(int(transfer(p,0_c_intptr_t),c_int64_t),int(z'FFFFFFFF',c_int64_t))
  end function
end program
