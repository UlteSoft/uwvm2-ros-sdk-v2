program processor
  use wros_scene, only: wr_abi
  use iso_c_binding
  implicit none
  integer(c_int32_t) :: samples(8), i, scalar
  interface
    subroutine check_samples(first, scalar, width, fast16, version) bind(c)
      import c_int32_t
      integer(c_int32_t), intent(in) :: first(8)
      integer(c_int32_t), intent(inout) :: scalar
      integer(c_int32_t), value :: width, fast16, version
    end subroutine
    function sample_value() bind(c)
      import c_double
      real(c_double) :: sample_value
    end function
    subroutine check_scalar(value) bind(c)
      import c_int32_t
      integer(c_int32_t), value :: value
    end subroutine
  end interface
  do i = 1, size(samples)
    samples(i) = i*i+2
  end do
  scalar = 17
  call check_samples(samples, scalar, c_size_t+c_intptr_t+c_long, c_int_fast16_t, wr_abi())
  call check_scalar(scalar + exponent(sample_value()))
end program
