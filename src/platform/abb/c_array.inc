typedef struct { const @TYPE@ *values; size_t count; uwrosv2_abb_ros1_string wire; } @TYPE@_array;
typedef struct { const @TYPE@ *values; size_t remaining; uwrosv2_abb_ros1_reader wire; } @TYPE@_iterator;
/** Borrow count readable typed @QUALIFIED@ elements for encoding. Keep them alive while using the sequence. */
static inline @TYPE@_array @TYPE@_array_values(const @TYPE@ *values, size_t count) UWROSV2_ABB_ROS1_NOEXCEPT {
    @TYPE@_array result = {values, count, {NULL, 0}};
    return result;
}
/** Start a forward iterator on a decoded wire view or a caller-owned array of @QUALIFIED@ records. */
static inline @TYPE@_iterator @TYPE@_array_iter(const @TYPE@_array *array) UWROSV2_ABB_ROS1_NOEXCEPT {
    @TYPE@_iterator iter = {array->values, array->count, {array->wire.data, array->wire.size, 0}};
    return iter;
}
/** Read one @QUALIFIED@ element. Returns 1 after updating out and 0 at the end or on invalid data. */
static inline int @TYPE@_array_next(@TYPE@_iterator *iter, @TYPE@ *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    @TYPE@ value;
    if (!iter || !out || !iter->remaining) return 0;
    if (iter->values) value = *iter->values++;
    else if (!@TYPE@_read(&iter->wire, &value)) return 0;
    --iter->remaining;
    *out = value;
    return 1;
}
static inline int @TYPE@_array_scan(uwrosv2_abb_ros1_reader *r, size_t count) UWROSV2_ABB_ROS1_NOEXCEPT {
    @TYPE@ value;
    if (count > (r->size - r->pos) / @MINIMUM@) return 0;
    while (count--) if (!@TYPE@_read(r, &value)) return 0;
    return 1;
}
static inline int @TYPE@_array_read(uwrosv2_abb_ros1_reader *r, @TYPE@_array *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    uint32_t count;
    size_t start;
    if (!uwrosv2_abb_ros1_get_uint32(r, &count)) return 0;
    start = r->pos;
    if (!@TYPE@_array_scan(r, count)) return 0;
    out->values = NULL;
    out->count = count;
    out->wire.data = r->data + start;
    out->wire.size = r->pos - start;
    return 1;
}
static inline int @TYPE@_array_write(uwrosv2_abb_ros1_writer *w, const @TYPE@_array *array) UWROSV2_ABB_ROS1_NOEXCEPT {
    size_t i;
    if (array->count != (uint32_t)array->count || !uwrosv2_abb_ros1_put_word(w, 4, array->count)) return 0;
    if (array->values) {
        if (array->wire.size || array->count > (w->capacity - w->pos) / @MINIMUM@) return 0;
        for (i = 0; i < array->count; ++i) if (!@TYPE@_write(w, array->values + i)) return 0;
        return 1;
    } else {
        uwrosv2_abb_ros1_reader r = {array->wire.data, array->wire.size, 0};
        return @TYPE@_array_scan(&r, array->count) && r.pos == r.size
            && uwrosv2_abb_ros1_put_bytes(w, r.data, r.size);
    }
}
