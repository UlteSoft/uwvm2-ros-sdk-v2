#include "visibility.h"
#include "objc/runtime.h"
#include "gc_ops.h"
#include "class.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static id allocate_class(Class cls, size_t extraBytes)
{
	size_t size;
	if (__builtin_add_overflow((size_t)cls->instance_size, extraBytes, &size) ||
	    __builtin_add_overflow(size, sizeof(intptr_t), &size))
	{
		return nil;
	}
#ifdef _WIN32
	intptr_t *addr = _aligned_malloc(size, 32);
	if (addr != NULL) memset(addr, 0, size);
#else
	intptr_t *addr = calloc(size, 1);
#endif
	return addr == NULL ? nil : (id)(addr + 1);
}

static void free_object(id obj)
{
#ifdef _WIN32
	_aligned_free((void*)(((intptr_t*)obj) - 1));
#else
	free((void*)(((intptr_t*)obj) - 1));
#endif
}

static void *alloc(size_t size)
{
	return calloc(size, 1);
}

void objc_registerThreadWithCollector(void) {}
void objc_unregisterThreadWithCollector(void) {}
void objc_assertRegisteredThreadWithCollector() {}

PRIVATE struct gc_ops gc_ops_none = 
{
	.allocate_class = allocate_class,
	.free_object    = free_object,
	.malloc         = alloc,
	.free           = free
};
PRIVATE struct gc_ops *gc = &gc_ops_none;

void objc_set_collection_threshold(size_t threshold) {}
void objc_set_collection_ratio(size_t ratio) {}
void objc_collect(unsigned long options) {}
BOOL objc_collectingEnabled(void) { return NO; }
BOOL objc_atomicCompareAndSwapPtr(id predicate, id replacement, volatile id *objectLocation)
{
	return __sync_bool_compare_and_swap(objectLocation, predicate, replacement);
}
BOOL objc_atomicCompareAndSwapPtrBarrier(id predicate, id replacement, volatile id *objectLocation)
{
	return __sync_bool_compare_and_swap(objectLocation, predicate, replacement);
}

BOOL objc_atomicCompareAndSwapGlobal(id predicate, id replacement, volatile id *objectLocation)
{
	return objc_atomicCompareAndSwapPtr(predicate, replacement, objectLocation);
}
BOOL objc_atomicCompareAndSwapGlobalBarrier(id predicate, id replacement, volatile id *objectLocation)
{
	return objc_atomicCompareAndSwapPtr(predicate, replacement, objectLocation);
}
BOOL objc_atomicCompareAndSwapInstanceVariable(id predicate, id replacement, volatile id *objectLocation)
{
	return objc_atomicCompareAndSwapPtr(predicate, replacement, objectLocation);
}
BOOL objc_atomicCompareAndSwapInstanceVariableBarrier(id predicate, id replacement, volatile id *objectLocation)
{
	return objc_atomicCompareAndSwapPtr(predicate, replacement, objectLocation);
}

id objc_assign_strongCast(id val, id *ptr)
{
	*ptr = val;
	return val;
}

id objc_assign_global(id val, id *ptr)
{
	*ptr = val;
	return val;
}

id objc_assign_ivar(id val, id dest, ptrdiff_t offset)
{
	*(id*)((char*)dest+offset) = val;
	return val;
}

void *objc_memmove_collectable(void *dst, const void *src, size_t size)
{
	return memmove(dst, src, size);
}
id objc_read_weak(id *location)
{
	return *location;
}
id objc_assign_weak(id value, id *location)
{
	*location = value;
	return value;
}
id objc_allocate_object(Class cls, int extra)
{
	return class_createInstance(cls, extra);
}

BOOL objc_collecting_enabled(void) { return NO; }
void objc_startCollectorThread(void) {}
void objc_clear_stack(unsigned long options) {}
BOOL objc_is_finalized(void *ptr) { return NO; }
void objc_finalizeOnMainThread(Class cls) {}
