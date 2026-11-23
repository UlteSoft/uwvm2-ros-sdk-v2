#pragma once
#include <objc/runtime.h>

/** A manually owned, single-threaded guest object. Subclasses inherit a GNUstep isa slot. */
__attribute__((objc_root_class))
@interface UWRObject {
@private
    Class isa;
}
/** Allocate and zero an instance of the receiving class. Returns nil if allocation fails. */
+ (instancetype)create;
/** Destroy this instance and release its guest storage. Discard all outstanding references. */
- (void)dispose;
@end
