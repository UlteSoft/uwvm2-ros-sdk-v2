! The test deployer supplies a serialized request for its simulated joint,
! the byte offset of the target, and the scenario's expected receiver state.
program humanoid
  use iso_c_binding
  use wros_scene
  use simulation
  implicit none
  interface
    subroutine abort_guest() bind(c, name="abort")
    end subroutine
  end interface
  character(kind=c_char), target :: alias(5)=['j','o','i','n','t']
  integer(c_int64_t), target :: handle=0, used=0, reply(64)=0, sequence
  integer(c_int64_t) :: bits
  integer(c_int) :: step, status

  call check(wr_capability_open(0_c_int, wr_address(c_loc(alias(1))), 5_c_int64_t, wr_address(c_loc(handle))) == 0)
  call check(poll(wr_driver_connect, 0_c_int64_t, 0_c_int64_t) == 0)
  do step=1,steps
    sequence=step
    call put_word(0, sequence)
    call put_word(32, sequence)
    if (success) then
      bits=transfer(merge(0.5_c_double, -0.5_c_double, btest(sequence,0)), bits)
      call put_word(target_offset, bits)
    end if
    call check(poll(wr_driver_submit, wr_address(c_loc(request)), int(size(request),c_int64_t)) == 0)
    status=poll(wr_driver_result, wr_address(c_loc(sequence)), 8_c_int64_t)
    if (crash) then
      call check(status==5 .or. status==13)
      call check(invoke(wr_driver_describe, 0_c_int64_t, 0_c_int64_t)==0)
      call check(used>=32 .and. reply(1)==6 .and. reply(4)==1)
    else
      call check(status==0 .and. used>=24 .and. reply(1)==merge(0,13,success) .and. reply(3)==sequence)
    end if
  end do
  call check(invoke(wr_driver_disconnect, 0_c_int64_t, 0_c_int64_t)==0)
contains
  subroutine check(ok)
    logical, intent(in) :: ok
    if (.not.ok) call abort_guest()
  end subroutine

  subroutine put_word(offset, word)
    integer, intent(in) :: offset
    integer(c_int64_t), intent(in) :: word
    integer :: octet, i
    do i=0,7
      octet=int(ibits(word,8*i,8))
      if (octet>127) octet=octet-256
      request(offset+i+1)=int(octet,c_int8_t)
    end do
  end subroutine

  integer(c_int) function invoke(operation,address,length)
    procedure(wr_driver_connect) :: operation
    integer(c_int64_t), value :: address, length
    invoke=operation(handle,0_c_int,address,length,wr_address(c_loc(reply)), &
                     int(c_sizeof(reply),c_int64_t),wr_address(c_loc(used)))
  end function

  integer(c_int) function poll(operation,address,length)
    procedure(wr_driver_connect) :: operation
    integer(c_int64_t), value :: address, length
    integer :: attempt
    do attempt=1,10000000
      poll=invoke(operation,address,length)
      if (poll/=11) return
    end do
    call abort_guest()
  end function
end program
