program lapack_numerics
  use wros_scene, only: wr_abi
  implicit none
  double precision, external :: dlapy3
  double precision :: version,magnitude,re,im
  interface
    subroutine abort_guest() bind(c,name="abort")
    end subroutine
  end interface
  version=dble(wr_abi())
  if (version/=2d0) call abort_guest()
  magnitude=dlapy3(version+1d0,version+2d0,version*6d0)
  if(abs(magnitude-13d0)>1d-12) call abort_guest()
  magnitude=dlapy3(3d200,4d200,12d200)*1d-200
  if(abs(magnitude-13d0)>1d-12) call abort_guest()
  magnitude=dlapy3(0d0,0d0,0d0)
  if(magnitude/=0d0) call abort_guest()
  call dladiv(3d0*version,version,version,-version,re,im)
  if(abs(re-1d0)+abs(im-2d0)>1d-12) call abort_guest()
end program
