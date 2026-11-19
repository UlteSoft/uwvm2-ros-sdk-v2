/**
 * @file pool.cpp
 * @brief Preserve independent allocation identities for mruby parser and compiler storage.
 *
 * Every returned block owns a libc allocation. An arena tracks lifetimes and
 * releases all remaining children on close. It does not split or recycle an
 * allocation. Metadata and payload belong to the same owner.
 */
#include <mruby.h>
#include <mruby/mempool.h>

#include <cstddef>
#include <cstring>

struct alignas(std::max_align_t) pool_block {
    pool_block *next;
    pool_block *previous;
    size_t size;
};

struct mempool {
    pool_block *first;
};

/** @brief Create an empty arena, returning null when memory is unavailable. */
mempool *mempool_open(void)
{
    auto *pool = static_cast<mempool *>(mrb_basic_alloc_func(nullptr, sizeof(mempool)));
    if (pool) pool->first = nullptr;
    return pool;
}

/** @brief Retire every block using the selected Wasm allocator. */
void mempool_close(mempool *pool)
{
    if (!pool) return;
    for (auto *block = pool->first; block;) {
        auto *next = block->next;
        mrb_basic_alloc_func(block, 0);
        block = next;
    }
    mrb_basic_alloc_func(pool, 0);
}

/** @brief Allocate one independently owned, aligned payload. */
void *mempool_alloc(mempool *pool, size_t size)
{
    if (!pool || size > SIZE_MAX - sizeof(pool_block)) return nullptr;
    size_t capacity = size ? size : 1;
    auto *block = static_cast<pool_block *>(mrb_basic_alloc_func(nullptr, sizeof(pool_block) + capacity));
    if (!block) return nullptr;
    *block = {pool->first, nullptr, size};
    if (pool->first) pool->first->previous = block;
    pool->first = block;
    return block + 1;
}

/** @brief Grow a block without losing the original ownership on allocation failure. */
void *mempool_realloc(mempool *pool, void *data, size_t old_size, size_t new_size)
{
    if (!pool) return nullptr;
    if (!data) return old_size ? nullptr : mempool_alloc(pool, new_size);
    if (new_size <= old_size) return data;
    auto *block = static_cast<pool_block *>(data) - 1;
    if (old_size > block->size) return nullptr;
    auto *larger = mempool_alloc(pool, new_size);
    if (!larger) return nullptr;
    if (old_size) std::memcpy(larger, data, old_size);
    if (block->previous) block->previous->next = block->next;
    else pool->first = block->next;
    if (block->next) block->next->previous = block->previous;
    mrb_basic_alloc_func(block, 0);
    return larger;
}
