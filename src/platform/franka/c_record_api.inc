/** Measure an encapsulated frame, including its four-byte CDR header. */
static inline int @t@_encoded_size(const @t@ *value, size_t *size) @NX@ {
    @p@writer w = {NULL, (size_t)-1 - 4, 0, @p@little_endian};
    if (!value || !size || !@t@_put(&w, value)) return 0;
    *size = 4 + w.pos;
    return 1;
}

/** Fill caller-owned disjoint storage. The frame and byte count are committed after preflight. */
static inline int @t@_encode(const @t@ *value, @p@endian order, uint8_t *data,
                               size_t capacity, size_t *written) @NX@ {
    size_t needed;
    if (!data || !written || (order != @p@little_endian && order != @p@big_endian) ||
        !@t@_encoded_size(value, &needed) || needed > capacity) return 0;
    @p@writer w = {data + 4, needed - 4, 0, order};
    if (!@t@_put(&w, value)) return 0;
    @p@write_header(data, order);
    *written = needed;
    return 1;
}

/** Validate all fields before assigning out. Its variable fields borrow the immutable frame. */
static inline int @t@_decode(const uint8_t *data, size_t size, @t@ *out) @NX@ {
    @p@reader r;
    @t@ value;
    if (!out || !@p@begin_read(&r, data, size) || !@t@_get(&r, &value) || !@p@end_read(&r)) return 0;
    *out = value;
    return 1;
}

static inline int @t@_validate(const uint8_t *data, size_t size) @NX@ {
    @p@reader r;
    @t@ value;
    return @p@begin_read(&r, data, size) && @t@_get(&r, &value) && @p@end_read(&r);
}
