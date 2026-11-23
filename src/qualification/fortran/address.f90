program address_test
  use iso_c_binding
  use wros_scene, only: wr_address, wr_capability_open, wr_capability_close
  implicit none
  character(kind=c_char, len=6), target :: alias
  integer(c_int64_t), target :: handle
  integer(c_int32_t) :: status
  interface
    function sample_address() bind(c)
      import c_ptr
      type(c_ptr) :: sample_address
    end function
    subroutine check_address(value) bind(c)
      import c_int64_t
      integer(c_int64_t), value :: value
    end subroutine
    subroutine check_status(status) bind(c)
      import c_int32_t
      integer(c_int32_t), value :: status
    end subroutine
  end interface
  ! The permanent test pattern covers bit 31/63 without dereferencing it.
  call check_address(wr_address(sample_address()))
  alias = 'signal'
  handle = 0
  status = wr_capability_open(0, wr_address(c_loc(alias)), 6_c_int64_t, wr_address(c_loc(handle)))
  call check_status(status)
  call check_status(wr_capability_close(handle))
end program
