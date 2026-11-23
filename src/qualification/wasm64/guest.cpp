#include <charconv>
#include <cstdlib>
#include <string>

static_assert(sizeof(void *) == 8 && sizeof(std::size_t) == 8, "expected memory64 C++ ABI");

static volatile double decimal = 1.25;
static volatile int error_code = 29;
static volatile int unwound = 0;

struct MarkUnwind {
    ~MarkUnwind() { unwound = 1; }
};

[[gnu::noinline]] static void throw_error()
{
    MarkUnwind marker;
    throw error_code;
}

int main()
{
    char formatted[16];
    auto result = std::to_chars(formatted, formatted + sizeof(formatted), decimal,
                                std::chars_format::fixed, 3);
    if (result.ec != std::errc{})
        return 74;
    std::string message("WROS libc++ memory64 conversion: ");
    message.append(formatted, result.ptr);
    if (message != "WROS libc++ memory64 conversion: 1.250")
        return 75;

    try {
        throw_error();
    } catch (int code) {
        message.clear();
        std::_Exit(code == 29 && unwound == 1 ? 43 : 76);
    }
    return 77;
}
