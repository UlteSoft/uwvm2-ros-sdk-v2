!> @brief Check the ROSv2 ABI inside the guest and fail on mismatch.
program robot_status
  use iso_c_binding, only: c_int
  use wros_scene, only: wr_abi
  implicit none
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  integer(c_int), allocatable :: samples(:)
  integer(c_int) :: count, rc

  count = wr_abi()
  if (count /= 2) call abort_guest()
  allocate(samples(count), stat=rc)
  if (rc /= 0) call abort_guest()
  samples = 21
  if (samples(1) + samples(count) /= 42) call abort_guest()
  deallocate(samples, stat=rc)
  if (rc /= 0) call abort_guest()
end program
