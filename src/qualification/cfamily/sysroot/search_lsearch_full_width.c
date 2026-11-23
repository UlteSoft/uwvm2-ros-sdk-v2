/*
 * Port of libc-test src/functional/search_lsearch.c.
 * Copyright © 2005-2013 libc-test AUTHORS. See ../upstream/libc-test/COPYRIGHT.
 */
#ifndef _XOPEN_SOURCE
#define _XOPEN_SOURCE 700
#endif
#include <search.h>
#include <string.h>
#include "test.h"

typedef char record[80];
static record table[100];
static const record initial[] = { "", "a", "b", "abc", "cd", "e", "ef", "g", "h", "iiiiiiiiii" };
static const record missing = "c";
static const record duplicate = "g";
static const record added = "j";

static int compare_strings(const void *a, const void *b)
{
    return strcmp(a, b);
}

int main(void)
{
    size_t count = 0;
    const size_t initial_count = sizeof initial / sizeof initial[0];

    /* Make a short copy detectable even in the zero-padded part of a record. */
    memset(table, 0xa5, sizeof table);
    for (size_t i = 0; i < initial_count; ++i) {
        void *entry = lsearch(initial[i], table, &count, sizeof(record), compare_strings);
        if (count != i + 1 || entry != table[i] || memcmp(entry, initial[i], sizeof(record)) != 0) {
            t_error("lsearch failed to append the full record for '%s' at %zu\n", initial[i], i);
            return t_status;
        }
    }

    if (lfind(initial[1], table, &count, sizeof(record), compare_strings) != table[1] ||
        count != initial_count) {
        t_error("lfind failed to find 'a' with the original table size\n");
        return t_status;
    }
    if (lfind(missing, table, &count, sizeof(record), compare_strings) != NULL ||
        count != initial_count) {
        t_error("lfind should miss 'c' and preserve the table size\n");
        return t_status;
    }
    if (lsearch(duplicate, table, &count, sizeof(record), compare_strings) != table[7] ||
        count != initial_count) {
        t_error("lsearch should return the existing 'g' and preserve the table size\n");
        return t_status;
    }

    void *entry = lsearch(added, table, &count, sizeof(record), compare_strings);
    if (count != initial_count + 1 || entry != table[initial_count] ||
        memcmp(entry, added, sizeof(record)) != 0)
        t_error("lsearch failed to append the full record for 'j'\n");
    return t_status;
}
