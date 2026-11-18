program check_clocks
  use expected_clocks, only: elapsed, cpu
  implicit none
  integer(8) :: ticks, rate, maximum
  integer(4) :: short_ticks, short_rate, short_maximum
  real(8) :: process_seconds
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  call system_clock(ticks, rate, maximum)
  call system_clock(short_ticks, short_rate, short_maximum)
  call cpu_time(process_seconds)
  if (elapsed) then
    if (ticks < 0 .or. rate /= 1000000000_8 .or. maximum /= huge(ticks)) call abort_guest()
    if (short_ticks < 0 .or. short_rate /= 1000 .or. short_maximum /= huge(short_ticks)) call abort_guest()
  else
    if (ticks /= -huge(ticks) .or. rate /= 0 .or. maximum /= 0) call abort_guest()
    if (short_ticks /= -huge(short_ticks) .or. short_rate /= 0 .or. short_maximum /= 0) call abort_guest()
  end if
  if ((process_seconds >= 0d0) .neqv. cpu) call abort_guest()
end program
