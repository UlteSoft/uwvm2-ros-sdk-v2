#include <malloc.h>
#include <stdint.h>

struct extent {
    uintptr_t address;
    size_t capacity;
    unsigned tag;
};
static struct extent allocated[2];

static struct extent observe(int *pointer, size_t capacity) {
    uintptr_t address = (uintptr_t)__builtin_wasm_memtag_untag(0, pointer);
    unsigned tag = __builtin_wasm_memtag_extract(0, pointer);
    if (capacity < 4 * sizeof(int) || ((address | capacity) & 15u))
        __builtin_trap();
    return (struct extent){address, capacity, tag};
}

static void verify(int *a, int *b, int n, struct extent left, struct extent right) {
    if (n != 4 || a[0] + b[n - 1] != 42)
        __builtin_trap();
    struct extent low = left.address < right.address ? left : right;
    struct extent high = left.address < right.address ? right : left;
    uintptr_t distance = high.address - low.address;
    if (distance < low.capacity || distance - low.capacity > 64)
        __builtin_trap();
    if (__builtin_wasm_memtag_status(0) && (!low.tag || !high.tag || low.tag == high.tag))
        __builtin_trap();
}

void check_static(int *a, int *b, int n) {
    verify(a, b, n, observe(a, 4 * sizeof(int)), observe(b, 4 * sizeof(int)));
}

void check_allocatable(int *a, int *b, int n) {
    /* Flang may request more bytes than the declared array to meet its
       alignment requirement. Physical neighbors are measured from the end of
       the allocator's registered range. */
    allocated[0] = observe(a, malloc_usable_size(a));
    allocated[1] = observe(b, malloc_usable_size(b));
    verify(a, b, n, allocated[0], allocated[1]);
}

void check_deallocation(void) {
    /* Inspect shadow metadata through canonical integer addresses. The
       Fortran arrays have been deallocated and are never dereferenced. */
    for (unsigned object = 0; object < 2; ++object) {
        for (size_t byte = 0; byte < allocated[object].capacity; byte += 16) {
            void *address = (void *)(allocated[object].address + byte);
            if (__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, address)))
                __builtin_trap();
        }
    }
}
