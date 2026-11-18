#include <objc/runtime.h>
#include <stdint.h>
#include <wros/scene.h>

__attribute__((objc_root_class))
@interface Probe {
    Class isa;
    unsigned reading;
}
+ (id)make;
- (void)setReading:(unsigned)value;
- (unsigned)read;
@end
@implementation Probe
+ (id)make { return class_createInstance(self, 0); }
- (void)setReading:(unsigned)value { reading = value; }
- (unsigned)read { return reading; }
@end

@interface Calibrated : Probe
@end
@implementation Calibrated
- (unsigned)read { return [super read] + 2; }
@end

void _start(void) {
    Probe *instance = [Calibrated make];
    if (!instance) __builtin_trap();
    [instance setReading:40];
    if ([instance read] != 42 || [(Probe *)0 read] != 0) __builtin_trap();
#ifdef __WASM_MEMTAG__
    if (__builtin_wasm_memtag_status(0) && !__builtin_wasm_memtag_extract(0, instance))
        __builtin_trap();
#endif
    Class cls = object_getClass(instance);
    if (class_createInstance(cls, SIZE_MAX) != nil || object_dispose(nil) != nil)
        __builtin_trap();
    object_dispose(instance);
    char key[] = "signal";
    uint64_t cap = 0;
    if (wr_capability_open(0, (uintptr_t)key, sizeof(key) - 1, (uintptr_t)&cap) != 0 || !cap)
        __builtin_trap();
    if (wr_capability_close(cap) != 0 || wr_abi() != 2) __builtin_trap();
}
