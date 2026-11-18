/* Run the installed reader against a pack and independently encoded expectations.
 * expected.bin has repeated (key length, data length, FNV1a64, key bytes).
 * All guest tables are immutable core Wasm data. The runner grants no imports.
 */
#include <wros/package_resources.h>

static const unsigned char pack[] = {
#embed "resources.bin"
};
static const unsigned char expected[] = {
#embed "expected.bin"
};

static int check(void) {
    wros_package_index index;
    if (!wros_package_open(pack, sizeof pack, &index)) return 1;
    size_t off = 0;
    uint32_t matched = 0;
    while (off < sizeof expected) {
        if (sizeof expected - off < 16) return 2;
        uint32_t key = wros_package_u32(expected + off);
        uint32_t length = wros_package_u32(expected + off + 4);
        uint64_t checksum = wros_package_u32(expected + off + 8) |
                            (uint64_t)wros_package_u32(expected + off + 12) << 32;
        off += 16;
        if (key > sizeof expected - off) return 3;
        wros_package_view value;
        if (!wros_package_find(&index, (const char *)expected + off, key, &value) || value.size != length) return 4;
        uint64_t hash = UINT64_C(14695981039346656037);
        for (size_t i = 0; i < value.size; ++i) hash = (hash ^ value.bytes[i]) * UINT64_C(1099511628211);
        if (hash != checksum) return 5;
        off += key;
        ++matched;
    }
    wros_package_view absent;
    if (wros_package_find(&index, "file:///", 8, &absent) || absent.bytes || absent.size) return 6;
    if (matched != index.count) return 7;
    if (wros_package_open(pack, sizeof pack - 1, &index) || index.bytes || index.count) return 8;
    return 0;
}

#if defined(__wasm__)
void _start(void) { if (check()) __builtin_trap(); }
#else
int main(void) { return check(); }
#endif
