/* In tagged memory64, a 256-byte-aligned startup record leaves eight low
 * bits free in its 32-bit shared-memory offset. The parent's pointer tag
 * travels in those bits until the child restores it before its first load. */
#define WASI_THREAD_START_ALIGNMENT 256
#define WASI_THREAD_START_TAG_SHIFT 56
