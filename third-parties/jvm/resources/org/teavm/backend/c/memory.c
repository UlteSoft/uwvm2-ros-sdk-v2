#include "memory.h"
#include "heaptrace.h"
#include "definitions.h"
#include <stdlib.h>
#include <string.h>

#if TEAVM_UNIX
    #include <unistd.h>
    #include <sys/mman.h>
#endif

#if TEAVM_WINDOWS
    #include <Windows.h>
#endif

#if TEAVM_MEMORY_TRACE
    #include "heaptrace.h"
#endif

void* teavm_gc_heapAddress = NULL;
void* teavm_gc_gcStorageAddress = NULL;
int32_t teavm_gc_gcStorageSize = INT32_C(0);
void* teavm_gc_regionsAddress = NULL;
void* teavm_gc_cardTable = NULL;
int32_t teavm_gc_regionMaxCount;
int64_t teavm_gc_availableBytes;
int64_t teavm_gc_minAvailableBytes;
int64_t teavm_gc_maxAvailableBytes;
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
struct java_block {
    struct java_block *bucket_next;
    struct java_block *work_next;
    void *data;
    size_t bytes;
    unsigned marked;
};
static struct java_block *buckets[2048], *work;
static size_t heap_cap, charged, allocated_count, reclaimed_count;
static size_t bucket(void *p) {
    return ((uintptr_t)p >> 4) % 2048;
}
static struct java_block *lookup(void *p) {
    for (struct java_block *b=buckets[bucket(p)]; b; b=b->bucket_next) {
        if (b->data == p) return b;
    }
    return NULL;
}
void *wros_jvm_alloc(int32_t bytes) {
    if (bytes < 8 || (size_t)bytes > heap_cap) return NULL;
    size_t charge = (((size_t)bytes + 15) & ~(size_t)15) + sizeof(struct java_block);
    if (charge > heap_cap - charged) return NULL;
    struct java_block *b = calloc(1,sizeof(*b));
    if (!b) return NULL;
    b->data = calloc(1,bytes);
    if (!b->data) { free(b); return NULL; }
    #ifdef __WASM_MEMTAG__
    if (__builtin_wasm_memtag_status(0) && !__builtin_wasm_memtag_extract(0,b->data)) __builtin_trap();
#endif
    size_t i=bucket(b->data);
    b->bucket_next=buckets[i]; buckets[i]=b; b->bytes=bytes;
    charged+=charge;
    ++allocated_count;
    return b->data;
}
int32_t wros_jvm_enqueue(void *p) {
    struct java_block *b=lookup(p);
    if (!b || b->marked) return 0;
    b->marked=1;
    b->work_next=work;
    work=b;
    return 1;
}
int32_t wros_jvm_marked(void *p) {
    struct java_block *b=lookup(p);
    return p && (!b || b->marked);
}
void *wros_jvm_pop(void) {
    if (!work) return NULL;
    struct java_block *b=work;
    work=b->work_next;
    b->work_next=NULL;
    return b->data;
}
#include <malloc.h>
#ifdef __WASM_MEMTAG__
static uintptr_t physical(void *ptr) { return (uintptr_t)__builtin_wasm_memtag_untag(0, ptr); }
static unsigned check_java_owners(void) {
    unsigned seen=0;
    unsigned active=!!__builtin_wasm_memtag_status(0);
    for (size_t bucket_a=0; bucket_a<2048; ++bucket_a) {
        for (struct java_block *a=buckets[bucket_a]; a; a=a->bucket_next) {
            uintptr_t first=physical(a->data), size=malloc_usable_size(a->data);
            if (size<a->bytes || first+size<first) __builtin_trap();
            unsigned tag=__builtin_wasm_memtag_extract(0,a->data);
            if (!!tag!=active) __builtin_trap();
            for (size_t bucket_b=0; bucket_b<2048; ++bucket_b) {
                for (struct java_block *b=buckets[bucket_b]; b; b=b->bucket_next) {
                    uintptr_t next=physical(b->data);
                    if (next<=first || next-first<size || next-first-size>64) continue;
                    if (active && tag==__builtin_wasm_memtag_extract(0,b->data)) __builtin_trap();
                    ++seen;
                }
            }
        }
    }
    return seen;
}
#endif

void wros_jvm_sweep(void) {
    if (work) __builtin_trap();
    for (size_t i=0; i<2048; ++i) {
        struct java_block **head = &buckets[i];
        while (*head) {
            struct java_block *b=*head;
            if (b->marked) {
                b->marked=0;
                head=&b->bucket_next;
            } else {
                *head=b->bucket_next;
                const size_t bytes=b->bytes;
                volatile unsigned char *d=b->data;
                for (size_t n=0; n<bytes; ++n) d[n]=0;
                #ifdef __WASM_MEMTAG__
                uintptr_t retired = physical(b->data);
#endif
                free(b->data);
#ifdef __WASM_MEMTAG__
                if (__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, (void *)retired))) __builtin_trap();
#endif
                free(b);
                charged-=((bytes+15)&~(size_t)15)+sizeof(*b);
                ++reclaimed_count;
            }
        }
    }
}
int32_t wros_jvm_freebytes(void) { return (int32_t)(heap_cap-charged); }

void teavm_initHeap(int64_t min, int64_t max) {
    if (min<0 || min>max || max>INT32_MAX || heap_cap) __builtin_trap();
    heap_cap=max; teavm_gc_availableBytes=max; teavm_gc_maxAvailableBytes=max; teavm_gc_minAvailableBytes=min;
}
void teavm_gc_resizeHeap(int64_t n) { __builtin_trap(); }
typedef struct TeaVM_StaticGcRootDescriptor {
    void*** roots;
    int count;
} TeaVM_StaticGcRootDescriptor;

typedef struct TeaVM_StaticGcRootDescriptorTable {
    struct TeaVM_StaticGcRootDescriptorTable* next;
    int size;
    TeaVM_StaticGcRootDescriptor data[256];
} TeaVM_StaticGcRootDescriptorTable;

static TeaVM_StaticGcRootDescriptorTable *teavm_staticGcRootsBuilder = NULL;
static int teavm_staticGcRootDataSize = 0;
void*** teavm_gc_staticRoots;


void teavm_registerStaticGcRoots(void*** roots, int count) {
    if (count < 0 || teavm_gc_staticRoots || (uint32_t) count > INT32_MAX/sizeof(void**) - 1u - (uint32_t)teavm_staticGcRootDataSize) __builtin_trap();
    if (count == 0) {
        return;
    }

    TeaVM_StaticGcRootDescriptorTable* builder = teavm_staticGcRootsBuilder;
    if (builder == NULL || builder->size == 256) {
        builder = malloc(sizeof(TeaVM_StaticGcRootDescriptorTable));
        if (!builder) __builtin_trap();
        builder->size = 0;
        builder->next = teavm_staticGcRootsBuilder;
        teavm_staticGcRootsBuilder = builder;
    }

    int i = builder->size++;
    builder->data[i].roots = roots;
    builder->data[i].count = count;
    teavm_staticGcRootDataSize += count;
}

void teavm_initStaticGcRoots() {
    teavm_gc_staticRoots = malloc(sizeof(void**) * (teavm_staticGcRootDataSize + 1));

    if (!teavm_gc_staticRoots) __builtin_trap();
    void*** target = teavm_gc_staticRoots;
    *target++ = (void**) (intptr_t) teavm_staticGcRootDataSize;
    TeaVM_StaticGcRootDescriptorTable* builder = teavm_staticGcRootsBuilder;

    while (builder != NULL) {
        for (int j = 0; j < builder->size; ++j) {
            int count = builder->data[j].count;
            memcpy(target, builder->data[j].roots, count * sizeof(void**));
            target += count;
        }
        TeaVM_StaticGcRootDescriptorTable* next = builder->next;
        free(builder);
        builder = next;
    }
    teavm_staticGcRootsBuilder = NULL;
}

void wros_jvm_unsupported(void) { __builtin_trap(); }
