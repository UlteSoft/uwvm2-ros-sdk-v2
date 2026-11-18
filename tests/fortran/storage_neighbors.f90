module storage_samples
  use iso_c_binding
  implicit none
  integer(c_int), target, volatile, bind(c, name="wr_samples_left") :: left(4) = [17,13,11,7]
  integer(c_int), target, volatile, bind(c, name="wr_samples_right") :: right(4) = [5,3,2,25]
end module

program controller
  use storage_samples
  use wros_scene, only: wr_abi
  implicit none
  interface
    subroutine check_static(a,b,n) bind(c)
      import c_ptr,c_int
      type(c_ptr), value :: a,b
      integer(c_int), value :: n
    end subroutine
    subroutine check_allocatable(a,b,n) bind(c)
      import c_ptr,c_int
      type(c_ptr), value :: a,b
      integer(c_int), value :: n
    end subroutine
    subroutine check_deallocation() bind(c)
    end subroutine
  end interface
  integer(c_int), allocatable, target :: first(:), second(:)
  integer(c_int) :: i, n
  n=wr_abi()*2
  call check_static(c_loc(left), c_loc(right), n)
  allocate(first(n),second(n))
  do i=1,n
    first(i)=17
    second(i)=25
  end do
  call check_allocatable(c_loc(first),c_loc(second),n)
  deallocate(second,first)
  call check_deallocation()
end program
