program descriptor_status
  use iso_c_binding, only: c_int, c_intptr_t
  use wros_scene, only: wr_abi
  implicit none
  interface
    subroutine check_c_descriptor() bind(c)
    end subroutine
    subroutine check_status(ok) bind(c)
      import c_int
      integer(c_int), value :: ok
    end subroutine
  end interface
  integer(c_int), allocatable :: first(:), moved(:), empty(:)
  integer(c_int) :: rc,n
  integer(c_int), allocatable :: matrix(:,:)
  integer(c_int), pointer :: borrowed(:), owner(:)
  integer(c_intptr_t) :: wide
  character(len=96) :: msg
  n = wr_abi()+2
  call test(n==4)
  call check_c_descriptor()
  nullify(owner,borrowed)
  allocate(owner(n),stat=rc)
  call test(rc==0.and.associated(owner))
  borrowed => owner
  borrowed(n)=42
  call test(owner(n)==42.and.associated(borrowed,owner))
  nullify(borrowed)
  deallocate(owner,stat=rc)
  call test(rc==0.and..not.associated(owner))
  ! These shapes are not representable at the selected guest pointer width.
  ! No large allocation is necessary to exercise the checked shape path.
  if (bit_size(wide) == 32) then
    ! Occupied bounds must survive conversion into a CFI_index_t. These
    ! would become the small valid bounds 1:2 if converted before checking.
    allocate(matrix(4294967297_8:4294967298_8,1),stat=rc)
    call test(rc/=0.and..not.allocated(matrix))
    ! An empty interval canonicalizes to extent zero before the width check.
    allocate(matrix(-4294967296_8:-4294967297_8,1),stat=rc)
    call test(rc==0.and.allocated(matrix).and.size(matrix)==0)
    deallocate(matrix,stat=rc)
    call test(rc==0)
  end if
  wide = huge(wide) / int(n, c_intptr_t) + 1
  allocate(matrix(wide,2),stat=rc)
  call test(rc/=0.and..not.allocated(matrix))
  allocate(matrix(-huge(wide):huge(wide),1),stat=rc)
  call test(rc/=0.and..not.allocated(matrix))
  allocate(matrix(2,3),stat=rc)
  call test(rc==0.and.allocated(matrix))
  matrix=7
  call test(matrix(2,3)==7)
  deallocate(matrix,stat=rc)
  call test(rc==0)
  allocate(first(0:n-1),stat=rc)
  call test(rc==0.and.allocated(first))
  first=17
  msg=' '
  allocate(first(n+1),stat=rc,errmsg=msg)
  call test(rc/=0.and.len_trim(msg)>0.and.size(first)==n)
  call test(lbound(first,1)==0.and.first(0)==17.and.first(n-1)==17)
  call move_alloc(first,moved,stat=rc)
  call test(rc==0.and..not.allocated(first).and.allocated(moved))
  call test(lbound(moved,1)==0.and.moved(n-1)==17)
  deallocate(moved,stat=rc)
  call test(rc==0.and..not.allocated(moved))
  deallocate(moved,stat=rc)
  call test(rc/=0)
  allocate(empty(0),stat=rc)
  call test(rc==0.and.allocated(empty).and.size(empty)==0)
  deallocate(empty,stat=rc)
  call test(rc==0)
contains
  subroutine test(ok)
    logical, intent(in) :: ok
    call check_status(merge(1_c_int,0_c_int,ok))
  end subroutine
end program
