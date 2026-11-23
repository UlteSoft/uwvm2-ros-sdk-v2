#include <uwrosv2/objc/Object.h>

@implementation UWRObject
+ (instancetype)create {
    return class_createInstance(self, 0);
}
- (void)dispose {
    object_dispose(self);
}
@end
