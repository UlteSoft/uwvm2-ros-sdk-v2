#import <objc/runtime.h>
#include <cstdio>

__attribute__((objc_root_class))
@interface ExceptionBase { Class isa; }
@end
@implementation ExceptionBase
@end
@interface ExceptionChild : ExceptionBase
@end
@implementation ExceptionChild
@end
__attribute__((objc_root_class))
@interface UnrelatedException { Class isa; }
@end
@implementation UnrelatedException
@end

struct Cleanup {
    int &count;
    ~Cleanup() { ++count; }
};

__attribute__((noinline)) static void throwObject(id object, int &cleanups)
{
    Cleanup guard{cleanups};
    @throw object;
}

__attribute__((noinline)) static void throwNumber(int number)
{
    throw number;
}

int main()
{
    id object = class_createInstance(objc_getClass("ExceptionChild"), 0);
    if (!object)
        return 1;
    int cleanups = 0, objFinally = 0, cppFinally = 0, catches = 0;
    @try {
        @try {
            try {
                throwObject(object, cleanups);
            } catch (int) {
                return 2;
            } catch (...) {
                ++catches;
                throw;
            }
        } @catch (UnrelatedException *wrong) {
            return 3;
        } @catch (ExceptionBase *caught) {
            if (caught != object || cleanups != 1)
                return 4;
            ++catches;
            @throw;
        } @finally {
            ++objFinally;
        }
    } @catch (id caught) {
        if (caught != object)
            return 5;
        ++catches;
    }
    try {
        @try {
            throwNumber(37);
        } @catch (id wrong) {
            return 6;
        } @catch (...) {
            ++catches;
            @throw;
        } @finally {
            ++cppFinally;
        }
    } catch (int number) {
        if (number != 37)
            return 7;
        ++catches;
    }
    object_dispose(object);
    if (objFinally != 1 || cppFinally != 1 || cleanups != 1 || catches != 5)
        return 8;
    std::puts("mixed-objc-cxx-eh-ok");
    return 0;
}
