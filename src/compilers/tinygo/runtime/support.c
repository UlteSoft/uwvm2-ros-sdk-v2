typedef __SIZE_TYPE__ usize;

// syscall.getErrno reads this wasi-libc data symbol directly. TinyGo's cgo
// runtime reads the same cell through __errno_location on this unthreaded ABI.
__attribute__((weak)) int errno;
__attribute__((weak)) int *__errno_location(void) {
    return &errno;
}

struct wasi_ciovec {
    const void *base;
    usize length;
};

__attribute__((import_module("wasi_snapshot_preview1"), import_name("fd_write")))
extern unsigned wasi_fd_write(unsigned fd, const struct wasi_ciovec *iov, usize count, usize *written);

// The ordinary Go os.File and fmt APIs use POSIX write. Preserve the caller's
// descriptor, the Preview1 permission result, and any short successful write.
__attribute__((weak)) __PTRDIFF_TYPE__ write(int fd, const void *data, usize length) {
    struct wasi_ciovec iov = {data, length};
    usize written = 0;
    unsigned status = wasi_fd_write((unsigned)fd, &iov, 1, &written);
    if (status) {
        errno = (int)status;
        return -1;
    }
    return (__PTRDIFF_TYPE__)written;
}

__attribute__((weak)) int memcmp(const void *left, const void *right, usize size) {
    const unsigned char *a = left, *b = right;
    for (usize i = 0; i < size; ++i) {
        if (a[i] != b[i]) return (int)a[i] - (int)b[i];
    }
    return 0;
}

__attribute__((weak)) usize strlen(const char *s) {
    usize length = 0;
    while (s[length] != '\0') ++length;
    return length;
}
