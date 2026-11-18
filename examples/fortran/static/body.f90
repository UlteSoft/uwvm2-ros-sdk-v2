program app
  use ISO_C_binding
  use wros_scene, only: wr_abi
  implicit none
  interface
    function sumsq(n,values) bind(c) result(value)
      import
      integer(c_int), value :: n
      real(c_double) :: values(n),value
    end function
    subroutine fail() bind(c,name="abort")
    end subroutine
  end interface
  real(c_double) :: raw(4)
  raw=real(wr_abi(),c_double)+[1,2,3,4]
  if (sumsq(4,raw)/=86.0_c_double) call fail()
end program
