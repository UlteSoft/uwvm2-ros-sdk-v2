#include <objc/runtime.h>
#include <stdint.h>
#include <malloc.h>

__attribute__((objc_root_class))
@interface Packet { Class isa; unsigned sequence; }
+ (id)createWithExtra:(uintptr_t)count;
- (void)setSequence:(unsigned)n;
- (unsigned)getSequence;
@end
@implementation Packet
+ (id)createWithExtra:(uintptr_t)count { return class_createInstance(self, count); }
- (void)setSequence:(unsigned)n { sequence = n; }
- (unsigned)getSequence { return sequence; }
@end

static unsigned char first_global[16] __attribute__((aligned(16)));
static unsigned char second_global[16] __attribute__((aligned(16)));
// Keep independent objects live across an opaque call in optimized Wasm.
__attribute__((noinline,optnone))
static unsigned compare(void *a, void *b, uintptr_t size) {
    uintptr_t ap = (uintptr_t)__builtin_wasm_memtag_untag(0, a);
    uintptr_t bp = (uintptr_t)__builtin_wasm_memtag_untag(0, b);
    unsigned at = __builtin_wasm_memtag_extract(0, a);
    unsigned bt = __builtin_wasm_memtag_extract(0, b);
    unsigned active = __builtin_wasm_memtag_status(0);
    if ((at != 0) != !!active || (bt != 0) != !!active) __builtin_trap();
    uintptr_t delta = ap > bp ? ap-bp : bp-ap;
    if (delta < size) __builtin_trap();
    if (delta-size > 64) return 0;
    if (active && at == bt) __builtin_trap();
    return 1;
}

void _start(void) {
    unsigned char stack_a[16] = {1}, stack_b[16] = {2};
    if (!compare(first_global, second_global, 16) || !compare(stack_a, stack_b, 16))
        __builtin_trap();
    Packet *live[32];
    uintptr_t sizes[32];
    unsigned compared = 0;
    for (unsigned round = 0; round < 5; ++round) {
        for (unsigned i = 0; i < 32; ++i) {
            live[i] = [Packet createWithExtra:round * 32];
            if (!live[i]) __builtin_trap();
            [live[i] setSequence:i+1];
            uintptr_t size = class_getInstanceSize(object_getClass(live[i]));
            if (size < sizeof(void *) + sizeof(unsigned)) __builtin_trap();
            // The pinned libobjc2 allocator returns the address immediately
            // following its intptr_t reference count. Its ownership extent
            // includes both this prefix and any requested indexed ivars.
            intptr_t *base = (intptr_t *)(void *)live[i] - 1;
            sizes[i] = malloc_usable_size(base);
            if (sizes[i] < sizeof(intptr_t) + size + round * 32) __builtin_trap();
            for (unsigned j = 0; j < i; ++j) {
                intptr_t *peer = (intptr_t *)(void *)live[j] - 1;
                uintptr_t a = (uintptr_t)__builtin_wasm_memtag_untag(0, base);
                uintptr_t b = (uintptr_t)__builtin_wasm_memtag_untag(0, peer);
                compared += compare(base, peer, a < b ? sizes[i] : sizes[j]);
            }
        }
        for (unsigned i = 0; i < 32; ++i) {
            if ([live[i] getSequence] != i+1) __builtin_trap();
            uintptr_t physical = (uintptr_t)__builtin_wasm_memtag_untag(0, live[i]);
            object_dispose(live[i]);
            if (__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, (void *)physical))) __builtin_trap();
        }
    }
    if (compared < 64) __builtin_trap();
}
