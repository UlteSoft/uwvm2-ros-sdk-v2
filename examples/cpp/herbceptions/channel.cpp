struct range_error {
    unsigned channel;
};

unsigned channel_offset(unsigned channel) return_failure{range_error} {
    if (channel >= 8)
        return_failure(range_error{channel});
    return channel * 16;
}

extern "C" int offset(unsigned channel) {
    auto result = catch return_failure(channel_offset(channel));
    if (result.failed)
        return result.error.channel == channel ? -1 : -2;
    return static_cast<int>(result.value);
}

extern "C" void _start() {
    if (offset(3) != 48 || offset(9) != -1)
        __builtin_trap();
}
