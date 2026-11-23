/** A sequence of @label@. The elements borrow either a typed array or validated CDR storage. */
typedef struct {
    const @t@ *values;
    size_t count;
    @p@reader wire;
} @s@;
typedef struct {
    const @t@ *values;
    size_t remaining;
    @p@reader wire;
} @s@_iterator;

/** The caller keeps values[0..count) readable for the lifetime of this sequence. */
static inline @s@ @s@_values(const @t@ *values, size_t count) @NX@ {
    @s@ seq = {NULL, 0, {NULL, 0, 0, @p@big_endian, 0}};
    seq.values = values;
    seq.count = count;
    return seq;
}

static inline @s@_iterator @s@_iter(const @s@ *seq) @NX@ {
    @s@_iterator it = {seq->values, seq->count, seq->wire};
    return it;
}

/** Advance an iterator and assign one typed element on success. */
static inline int @s@_next(@s@_iterator *it, @t@ *out) @NX@ {
    if (!it || !out || !it->remaining) return 0;
    if (it->values) {
        *out = *it->values++;
    } else {
        @p@reader cursor = it->wire;
        @t@ value;
        if (!cursor.data || !@get@(&cursor, &value)) return 0;
        it->wire = cursor;
        *out = value;
    }
    --it->remaining;
    return 1;
}

static inline int @s@_get(@p@reader *r, @s@ *out, uint32_t bound) @NX@ {
    uint64_t count;
    if (!@p@get_word(r, 4, &count) || count > bound || count > (r->size - r->pos) / @min@u) return 0;
    @p@reader start = *r;
    for (size_t i = 0; i < (size_t)count; ++i) {
        @t@ value;
        if (!@get@(r, &value)) return 0;
    }
    start.size = r->pos;
    out->values = NULL;
    out->count = (size_t)count;
    out->wire = start;
    return 1;
}

static inline int @s@_put(@p@writer *w, const @s@ *seq, uint32_t bound) @NX@ {
    if (seq->count > bound || !@p@put_word(w, 4, seq->count)) return 0;
    if (seq->values) {
        for (size_t i = 0; i < seq->count; ++i) {
            if (!@put@(w, &seq->values[i])) return 0;
        }
        return 1;
    }
    /* Re-encode against the destination alignment origin and byte order. */
    @p@reader r = seq->wire;
    if (seq->count && !r.data) return 0;
    for (size_t i = 0; i < seq->count; ++i) {
        @t@ value;
        if (!@get@(&r, &value) || !@put@(w, &value)) return 0;
    }
    return r.pos == r.size;
}
