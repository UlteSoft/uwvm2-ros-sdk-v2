#import "base/apple/scoped_objc_class_swizzler.h"
#include <cstdio>

__attribute__((objc_root_class))
@interface SwizzleTarget { Class isa; }
- (int)score:(int)value;
- (int)replacement:(int)value;
+ (int)rank;
@end
@implementation SwizzleTarget
- (int)score:(int)value { return value + 7; }
- (int)replacement:(int)value { return value * 3; }
+ (int)rank { return 41; }
@end

__attribute__((objc_root_class))
@interface SwizzlePeer { Class isa; }
+ (int)rank;
@end
@implementation SwizzlePeer
+ (int)rank { return 73; }
@end

int main()
{
    using base::apple::ScopedObjCClassSwizzler;
    Class target = objc_getClass("SwizzleTarget");
    Class peer = objc_getClass("SwizzlePeer");
    SwizzleTarget *object = static_cast<SwizzleTarget *>(class_createInstance(target, 0));
    if (!object || [object score:5] != 12 || [object replacement:5] != 15)
        return 1;
    {
        ScopedObjCClassSwizzler swap(target, @selector(score:), @selector(replacement:));
        if ([object score:5] != 15 || [object replacement:5] != 12 ||
            swap.InvokeOriginal<int>(object, @selector(score:), 5) != 12)
            return 2;
    }
    if ([object score:5] != 12 || [object replacement:5] != 15 || [SwizzleTarget rank] != 41 || [SwizzlePeer rank] != 73)
        return 3;
    {
        ScopedObjCClassSwizzler swap(target, peer, @selector(rank));
        if ([SwizzleTarget rank] != 73 || [SwizzlePeer rank] != 41 ||
            swap.InvokeOriginal<int>(target, @selector(rank)) != 41)
            return 4;
    }
    if ([SwizzleTarget rank] != 41 || [SwizzlePeer rank] != 73)
        return 5;
    object_dispose(object);
    std::puts("chromium-scoped-objc-swizzler-ok");
    return 0;
}
