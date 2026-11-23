#import <objc/Object.h>
#import <objc/runtime.h>
#include <stdio.h>

// GCC's implementation supplies both selectors. The SDK supplies the root
// class declaration and the GNUstep object ABI used to compile the member.
@interface QualificationGCCObject (GCCMethods)
- (Class)class;
- (BOOL)isEqual:(id)other;
@end

@interface GCCChild : QualificationGCCObject
@end
@implementation GCCChild
@end

int main(void)
{
    Class root = objc_getClass("QualificationGCCObject");
    Class child = objc_getClass("GCCChild");
    if (!root || !child || class_getSuperclass(child) != root)
        return 1;
    QualificationGCCObject *first = class_createInstance(root, 0);
    QualificationGCCObject *second = class_createInstance(child, 0);
    if (!first || !second || [first class] != root || [second class] != child)
        return 2;
    if (![first isEqual:first] || ![second isEqual:second] || [first isEqual:second] || [first isEqual:nil])
        return 3;
    object_dispose(second);
    object_dispose(first);
    puts("gcc-libobjc-object-ok");
    return 0;
}
