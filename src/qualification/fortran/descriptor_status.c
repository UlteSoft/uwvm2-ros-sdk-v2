#include "flang/ISO_Fortran_binding.h"
#include <stdint.h>

void check_status(int ok) {
    if (!ok) __builtin_trap();
}

void check_c_descriptor(void) {
    CFI_CDESC_T(2) storage;
    CFI_cdesc_t *array = (CFI_cdesc_t *)&storage;
    CFI_index_t lower[] = {1, 1};
    CFI_index_t upper[] = {2, 3};
    CFI_index_t last[] = {2, 3};
    check_status(CFI_establish(array, 0, CFI_attribute_allocatable, CFI_type_int,
                               sizeof(int), 2, 0) == CFI_SUCCESS);
    check_status(CFI_allocate(array, lower, upper, 0) == CFI_SUCCESS);
    check_status(CFI_is_contiguous(array));
    int *element = CFI_address(array, last);
    *element = 42;
    check_status(((int *)array->base_addr)[5] == 42);
    check_status(CFI_deallocate(array) == CFI_SUCCESS && !array->base_addr);
    upper[0] = PTRDIFF_MAX;
    check_status(CFI_allocate(array, lower, upper, 0) == CFI_ERROR_MEM_ALLOCATION);
    check_status(!array->base_addr);
}
