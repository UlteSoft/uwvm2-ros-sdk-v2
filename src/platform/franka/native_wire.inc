/* Plain XCDRv1 aligns from the first payload byte, including across nested records.
 * A reader borrows an immutable payload. A writer with a null data pointer measures it. */
typedef enum { @p@big_endian = 0, @p@little_endian = 1 } @p@endian;
typedef struct { const uint8_t *data; size_t size; } @p@string;
typedef struct {
    const uint8_t *data;
    size_t size, pos;
    @p@endian order;
    uint8_t tail;
} @p@reader;
typedef struct {
    uint8_t *data;
    size_t size, pos;
    @p@endian order;
} @p@writer;
typedef char @p@requires_binary64[(sizeof(double) == 8 && CHAR_BIT == 8 &&
    FLT_RADIX == 2 && DBL_MANT_DIG == 53 && DBL_MAX_EXP == 1024) ? 1 : -1];

static inline int @p@begin_read(@p@reader *r, const uint8_t *data, size_t size) @NX@ {
    if (!data || size < 4 || data[0] != 0 || data[1] > 1 || data[2] != 0 || data[3] > 3) return 0;
    r->data = data + 4;
    r->size = size - 4;
    r->pos = 0;
    r->order = data[1] ? @p@little_endian : @p@big_endian;
    r->tail = data[3];
    return 1;
}

static inline int @p@end_read(const @p@reader *r) @NX@ {
    /* Some middleware removes the declared transport padding before handing off the sample. */
    if (r->pos > r->size || (r->tail && r->tail != ((0u - r->pos) & 3u))) return 0;
    return r->size == r->pos || r->size - r->pos == r->tail;
}

static inline void @p@write_header(uint8_t *out, @p@endian order) @NX@ {
    out[0] = 0;
    out[1] = (uint8_t)order;
    out[2] = 0;
    out[3] = 0;
}

static inline int @p@get_word(@p@reader *r, size_t width, uint64_t *out) @NX@ {
    const size_t pad = (0u - r->pos) & (width - 1);
    uint64_t value = 0;
    if (r->pos > r->size || pad + width > r->size - r->pos) return 0;
    r->pos += pad;
    for (size_t i = 0; i < width; ++i) {
        const size_t shift = 8 * (r->order == @p@little_endian ? i : width - 1 - i);
        value |= (uint64_t)r->data[r->pos + i] << shift;
    }
    r->pos += width;
    *out = value;
    return 1;
}

static inline int @p@put_word(@p@writer *w, size_t width, uint64_t value) @NX@ {
    const size_t pad = (0u - w->pos) & (width - 1);
    if (w->pos > w->size || pad + width > w->size - w->pos) return 0;
    if (w->data) {
        memset(w->data + w->pos, 0, pad);
        for (size_t i = 0; i < width; ++i) {
            const size_t shift = 8 * (w->order == @p@little_endian ? i : width - 1 - i);
            w->data[w->pos + pad + i] = (uint8_t)(value >> shift);
        }
    }
    w->pos += pad + width;
    return 1;
}

/* ROS IDL strings carry a uint32 count including the trailing NUL. Expose just the contents. */
static inline int @p@get_string(@p@reader *r, @p@string *out) @NX@ {
    uint64_t n;
    if (!@p@get_word(r, 4, &n) || n == 0 || n > r->size - r->pos) return 0;
    const size_t len = (size_t)n;
    if (r->data[r->pos + len - 1] != 0) return 0;
    out->data = r->data + r->pos;
    out->size = len - 1;
    r->pos += len;
    return 1;
}

static inline int @p@put_string(@p@writer *w, const @p@string *s) @NX@ {
    if ((!s->data && s->size) || s->size >= (uint32_t)-1) return 0;
    const size_t n = s->size + 1;
    if (!@p@put_word(w, 4, n) || n > w->size - w->pos) return 0;
    if (w->data) {
        if (s->size) memcpy(w->data + w->pos, s->data, s->size);
        w->data[w->pos + s->size] = 0;
    }
    w->pos += n;
    return 1;
}
