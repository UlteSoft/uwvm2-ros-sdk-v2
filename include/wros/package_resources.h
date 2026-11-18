#ifndef WROS_PACKAGE_RESOURCES_H
#define WROS_PACKAGE_RESOURCES_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

/** @brief Borrow an immutable buffer for the lifetime of the index and its views.
 * @details The pack contains a sorted table of exact package URIs and byte ranges.
 * The reader allocates no memory and makes no host calls. File selection belongs
 * to the pack producer. Any guest with the pack can read all its contents.
 */
typedef struct {
    const unsigned char *bytes;
    size_t size;
    uint32_t count;
} wros_package_index;

typedef struct {
    const unsigned char *bytes;
    size_t size;
} wros_package_view;

static inline uint32_t wros_package_u32(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static inline int wros_package_compare(const unsigned char *a, size_t an, const unsigned char *b, size_t bn) {
    int order = memcmp(a, b, an < bn ? an : bn);
    return order ? order : (an > bn) - (an < bn);
}

/** @brief Validate every range and the ordering before publishing an index.
 * @return 1 on success. On failure the output index is cleared.
 */
static inline int wros_package_open(const unsigned char *bytes, size_t size, wros_package_index *index) {
    if (!index) return 0;
    index->bytes = NULL;
    index->size = 0;
    index->count = 0;
    if (!bytes || size < 16 || size > 67108864 || memcmp(bytes, "WROSRES\0", 8)) return 0;
    uint32_t count = wros_package_u32(bytes + 8);
    size_t pos = wros_package_u32(bytes + 12);
    if (count > 65535 || pos != 16u + count * 16u || pos > size) return 0;
    const unsigned char *previous = NULL;
    size_t previous_size = 0;
    for (uint32_t i = 0; i < count; ++i) {
        const unsigned char *row = bytes + 16u + i * 16u;
        uint32_t key_size = wros_package_u32(row + 4);
        uint32_t data_size = wros_package_u32(row + 12);
        if (wros_package_u32(row) != pos || !key_size || key_size > 1024 || key_size > size - pos) return 0;
        const unsigned char *key = bytes + pos;
        if (previous && wros_package_compare(previous, previous_size, key, key_size) >= 0) return 0;
        previous = key;
        previous_size = key_size;
        pos += key_size;
        if (wros_package_u32(row + 8) != pos || data_size > size - pos) return 0;
        pos += data_size;
    }
    if (pos != size) return 0;
    index->bytes = bytes;
    index->size = size;
    index->count = count;
    return 1;
}

/** @brief Look up an exact URI in a previously opened immutable pack.
 * @return 1 for a present resource, including an empty file. A miss clears the view.
 */
static inline int wros_package_find(const wros_package_index *index, const char *uri, size_t length,
                                    wros_package_view *view) {
    if (!view) return 0;
    view->bytes = NULL;
    view->size = 0;
    if (!index || !index->bytes || !uri || !length || length > 1024) return 0;
    uint32_t lo = 0, hi = index->count;
    while (lo < hi) {
        uint32_t mid = lo + (hi - lo) / 2u;
        const unsigned char *row = index->bytes + 16u + mid * 16u;
        int order = wros_package_compare((const unsigned char *)uri, length,
                                         index->bytes + wros_package_u32(row), wros_package_u32(row + 4));
        if (order < 0) hi = mid;
        else if (order > 0) lo = mid + 1u;
        else {
            view->bytes = index->bytes + wros_package_u32(row + 8);
            view->size = wros_package_u32(row + 12);
            return 1;
        }
    }
    return 0;
}
#endif
