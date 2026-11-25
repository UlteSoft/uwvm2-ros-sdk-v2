#include <stdint.h>

/* Both reactors bind env.memory. The last page belongs to this ABI. */
typedef volatile unsigned char byte;
#define PUBLIC ((byte *)(uintptr_t)ABI_BASE)
#define SLOT ((byte *volatile *)(uintptr_t)(ABI_BASE + 16))
#define PAYLOAD(side) ((byte *)(uintptr_t)(ABI_BASE + 64 * (1 + (side))))
#define EXPORT(name) __attribute__((export_name(name)))

#if __has_builtin(__builtin_wasm_memtag_storez) != ABI_MTE
#error The installed compiler did not select the requested MTE profile
#endif

EXPORT("public_write") void public_write(unsigned value) { *PUBLIC = (unsigned char)value; }
EXPORT("public_read") unsigned public_read(void) { return *PUBLIC; }

EXPORT("publish") void publish(byte *p) { *SLOT = p; }
EXPORT("consume") byte *consume(void) { return *SLOT; }
EXPORT("advance") byte *advance(byte *p) { return p + 3; }
EXPORT("read_byte") unsigned read_byte(const byte *p) { return *p; }
EXPORT("write_byte") void write_byte(byte *p, unsigned value) { *p = (unsigned char)value; }

/* Each side can also construct the other payload's raw address from the protocol. */
EXPORT("peer_raw") byte *peer_raw(void) { return PAYLOAD(1 - ABI_SIDE) + 3; }

static byte *tag_pointer(byte *p) {
#if ABI_MTE
    return __builtin_wasm_memtag_insert(0, (void *)p, sizeof(p) == 4 ? 0xb : 0xab);
#else
    return p;
#endif
}

EXPORT("tag_public_pointer") byte *tag_public_pointer(void) { return tag_pointer(PUBLIC); }

EXPORT("prepare") byte *prepare(void) {
    byte *p = tag_pointer(PAYLOAD(ABI_SIDE));
#if ABI_MTE
    __builtin_wasm_memtag_storez(0, (void *)p, 16);
#else
    for (unsigned i = 0; i < 16; ++i)
        p[i] = 0;
#endif
    return p;
}
