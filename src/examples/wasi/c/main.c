#include <uwrosv2/wasi/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint8_t actual = 0;
        if (!uwrosv2_wasi_read_fs_filetype(data, size, &actual) || actual != 4) __builtin_trap();
        if (uwrosv2_wasi_read_fs_filetype(data, size - 1, &actual) || actual != 4) __builtin_trap();
    }
    {
        uint16_t actual = 0;
        if (!uwrosv2_wasi_read_fs_flags(data, size, &actual) || actual != 1) __builtin_trap();
        if (uwrosv2_wasi_read_fs_flags(data, size - 1, &actual) || actual != 1) __builtin_trap();
    }
    {
        uint64_t actual = 0;
        if (!uwrosv2_wasi_read_fs_rights_base(data, size, &actual) || actual != UINT64_C(66)) __builtin_trap();
        if (uwrosv2_wasi_read_fs_rights_base(data, size - 1, &actual) || actual != UINT64_C(66)) __builtin_trap();
    }
    {
        uint64_t actual = 0;
        if (!uwrosv2_wasi_read_fs_rights_inheriting(data, size, &actual) || actual != UINT64_C(4294967297)) __builtin_trap();
        if (uwrosv2_wasi_read_fs_rights_inheriting(data, size - 1, &actual) || actual != UINT64_C(4294967297)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
