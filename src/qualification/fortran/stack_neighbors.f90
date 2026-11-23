program controller
  implicit none
  interface
    subroutine inspect_fortran() bind(c)
    end subroutine
  end interface
  call inspect_fortran()
end program

subroutine capture_fortran(first, second, value) bind(c)
  use iso_c_binding
  implicit none
  integer(c_intptr_t), intent(out) :: first, second
  integer(c_int), intent(out) :: value
  integer(c_int), target, volatile :: left(4), right(4)

  left(1) = 17
  right(1) = 25
  first = transfer(c_loc(left), 0_c_intptr_t)
  second = transfer(c_loc(right), 0_c_intptr_t)
  value = left(1) + right(1)
end subroutine
