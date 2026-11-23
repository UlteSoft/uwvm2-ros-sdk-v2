/** Measure the serialized body of `@QUALIFIED@`.
 * @param value Record and readable spans for all referenced fields.
 * @param size Receives the exact byte count on success.
 * @return 1 on success, 0 for invalid values, missing arguments or an unrepresentable length.
 */
static inline int @TYPE@_encoded_size(const @TYPE@ *value, size_t *size) UWROSV2_ABB_ROS1_NOEXCEPT {
    uwrosv2_abb_ros1_writer measure = {NULL, UINT32_MAX, 0};
    if (!value || !size || !@TYPE@_write(&measure, value)) return 0;
    *size = measure.pos;
    return 1;
}
/** Encode `@QUALIFIED@` into caller-owned storage.
 * @param value Input record. Keep referenced strings, arrays and borrowed wire immutable during the call.
 * @param out Writable destination disjoint from all input spans. A zero-byte body permits a null pointer.
 * @param capacity Available destination bytes.
 * @param written Receives the byte count on success. Keep this count slot disjoint from the input and output.
 * @return 1 on success. On invalid input or insufficient capacity, returns 0 and preserves the destination and count.
 */
static inline int @TYPE@_encode(const @TYPE@ *value, uint8_t *out, size_t capacity, size_t *written) UWROSV2_ABB_ROS1_NOEXCEPT {
    size_t size;
    uwrosv2_abb_ros1_writer writer = {out, capacity, 0};
    if (!written || !@TYPE@_encoded_size(value, &size) || size > capacity || (size && !out)) return 0;
    if (!@TYPE@_write(&writer, value)) return 0;
    *written = size;
    return 1;
}
/** Decode one complete `@QUALIFIED@` body.
 * @param data Readable serialized bytes. An empty body permits a null pointer.
 * @param size Exact byte count. Nested lengths and complete consumption are checked.
 * @param out Receives a typed record on success. Keep the source alive and immutable while using borrowed fields.
 * @return 1 on success. Returns 0 for malformed or trailing data and preserves the output record.
 */
static inline int @TYPE@_decode(const uint8_t *data, size_t size, @TYPE@ *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    uwrosv2_abb_ros1_reader reader = {data, size, 0};
    @TYPE@ value;
    if (!out || (size && !data) || size != (uint32_t)size) return 0;
    if (!@TYPE@_read(&reader, &value) || reader.pos != size) return 0;
    *out = value;
    return 1;
}
/** Check the complete `@QUALIFIED@` body, including nested records and sequences.
 * @param data Readable serialized bytes. An empty body permits a null pointer.
 * @param size Exact byte count.
 * @return 1 for a valid body, 0 for an invalid argument, size, boolean, length or trailing bytes.
 */
static inline int @TYPE@_validate(const uint8_t *data, size_t size) UWROSV2_ABB_ROS1_NOEXCEPT {
    @TYPE@ value;
    return @TYPE@_decode(data, size, &value);
}
