module vector_kernel
  use iso_c_binding, only: c_double, c_int
  implicit none
contains
  subroutine transform(a, b, result, total, dotted, columns)
    real(c_double), intent(in) :: a(:,:), b(:,:)
    real(c_double), intent(out) :: result(:,:), total, dotted, columns(:)
    result=matmul(a, b)
    total=sum(result, mask=result>0.0_c_double)
    dotted=dot_product(a(:,2), b(2,:))
    columns=sum(result, dim=1)
  end subroutine
  subroutine discrete(a, b, result, total, dotted, mask)
    integer(c_int), intent(in) :: a(:,:), b(:,:)
    integer(c_int), intent(out) :: result(:,:), total, dotted
    logical, intent(out) :: mask(:,:)
    result=matmul(a,b)
    total=sum(result,mask=result>0)
    dotted=dot_product(a(:,2),b(2,:))
    mask=matmul(a>0,b>0)
  end subroutine
end module

program reduce_application
  use iso_c_binding, only: c_int, c_double
  use wros_scene, only: wr_abi
  use vector_kernel, only: transform, discrete
  implicit none
  interface
    subroutine abort_guest() bind(c,name="abort")
    end subroutine
  end interface
  integer(c_int) :: n
  real(c_double) :: a(2,2), b(2,2), result(2,2), total, dotted, columns(2)
  integer(c_int) :: discrete_result(2,2), discrete_total, discrete_product
  logical :: mask(2,2)
  n=wr_abi()
  if (n/=2) call abort_guest()
  a=reshape(real([n-1,n,n+1,n+2],c_double),[2,2])
  b=reshape(real([n,0,0,n],c_double),[2,2])
  call transform(a,b,result,total,dotted,columns)
  if (total/=20 .or. dotted/=8 .or. any(columns/=[6,14])) call abort_guest()
  if (any(result/=2*a)) call abort_guest()
  call discrete(int(a,c_int),int(b,c_int),discrete_result,discrete_total,discrete_product,mask)
  if (any(discrete_result/=int(result,c_int))) call abort_guest()
  if (discrete_total/=20.or.discrete_product/=8.or..not.all(mask)) call abort_guest()
  if (count(mask)/=4) call abort_guest()
end program
