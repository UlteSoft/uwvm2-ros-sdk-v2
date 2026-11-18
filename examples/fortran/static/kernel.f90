function sumsq(n, values) bind(c) result(score)
  use iso_c_binding
  implicit none
  integer(c_int), value :: n
  real(c_double) :: values(n), score
  score=dot_product(values(1:n:2),values(1:n:2))+dot_product(values(2:n:2),values(2:n:2))
end function
