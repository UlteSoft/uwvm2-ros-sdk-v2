#include <algorithm>
#include <atomic>
#include <bit>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <span>
#include <string_view>
#include <vector>

#if defined(BENCH_EXECUTION_MATRIX)
#include "guest.h"
#endif

#if defined(BENCH_PARSE)
#include <fast_float/fast_float.h>
#endif

namespace {
std::uint64_t monotonic_nanoseconds()
{
    timespec value{};
    if (clock_gettime(CLOCK_MONOTONIC, &value)) {
        std::abort();
    }
    return std::uint64_t(value.tv_sec) * 1000000000 + std::uint64_t(value.tv_nsec);
}

template<typename Work>
std::uint64_t measure(Work&& work)
{
    const auto start = monotonic_nanoseconds();
    std::atomic_signal_fence(std::memory_order_seq_cst);
    work();
    std::atomic_signal_fence(std::memory_order_seq_cst);
    const auto end = monotonic_nanoseconds();
    if (end <= start) {
        std::abort();
    }
    return end - start;
}

std::uint64_t hash_word(std::uint64_t hash, std::uint64_t word)
{
    return (hash ^ word) * UINT64_C(1099511628211);
}

std::uint32_t next_word(std::uint32_t& state)
{
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state;
}

#if defined(BENCH_SORT)
constexpr std::size_t block_size = 32768;
constexpr std::size_t blocks = 100;

[[gnu::noinline]] void sort_blocks(std::span<std::uint32_t> data)
{
    for (std::size_t offset = 0; offset < data.size(); offset += block_size) {
        auto block = data.subspan(offset, block_size);
        std::sort(block.begin(), block.end());
    }
}

void run()
{
    std::uint32_t seed = 0xc001d00d;
    std::vector<std::uint32_t> warm(block_size);
    std::vector<std::uint32_t> data(block_size * blocks);
    for (auto& word : warm) {
        word = next_word(seed);
    }
    for (auto& word : data) {
        word = next_word(seed);
    }
    sort_blocks(warm);
    const auto elapsed = measure([&] { sort_blocks(data); });

    std::uint64_t hash = UINT64_C(14695981039346656037);
    for (std::size_t offset = 0; offset < data.size(); offset += block_size) {
        const auto block = std::span(data).subspan(offset, block_size);
        if (!std::is_sorted(block.begin(), block.end())) {
            std::abort();
        }
        for (auto word : block) {
            hash = hash_word(hash, word);
        }
    }
    std::printf("cpp workload=sort items=%zu checksum=%016" PRIx64 " ns=%" PRIu64 "\n",
                data.size(), hash, elapsed);
}
#elif defined(BENCH_PARSE)
constexpr std::string_view decimals[] = {
    "1024", "-10.00099999999999", "3.141592653589793", "3.141592653589793238462643383",
    "0.84551240822557006", "9.999999999999998", "1000000000000000128", "-123456789.1234567",
    "1.7976931348623157e308", "2.2250738585072014e-308", "4.9406564584124654e-324", "0.00001376",
    "1e-24", "7.128274632e30", "993721e+12", "3.731389e-47",
};
constexpr std::size_t chunk_size = 16384;
#if defined(BENCH_EXECUTION_MATRIX)
constexpr std::size_t rounds = 16; // Fits the 128-page shared-memory owner at both guest widths.
#else
constexpr std::size_t rounds = 256;
#endif

[[gnu::noinline]] void parse_chunks(std::span<const std::string_view> inputs, std::span<double> outputs)
{
    for (std::size_t offset = 0; offset < outputs.size(); offset += inputs.size()) {
        for (std::size_t idx = 0; idx < inputs.size(); ++idx) {
            const auto token = inputs[idx];
            const auto end = token.data() + token.size();
            const auto result = fast_float::from_chars(token.data(), end, outputs[offset + idx]);
            if (result.ec != std::errc{} || result.ptr != end) {
                std::abort();
            }
        }
    }
}

void run()
{
    std::uint32_t seed = 0xc001d00d;
    std::vector<std::string_view> inputs(chunk_size);
    for (auto& token : inputs) {
        token = decimals[next_word(seed) % std::size(decimals)];
    }
    std::vector<double> warm(chunk_size);
    std::vector<double> output(chunk_size * rounds);
    parse_chunks(inputs, warm);
    const auto elapsed = measure([&] { parse_chunks(inputs, output); });

    std::uint64_t hash = UINT64_C(14695981039346656037);
    for (auto value : output) {
        hash = hash_word(hash, std::bit_cast<std::uint64_t>(value));
    }
    std::printf("cpp workload=parse items=%zu checksum=%016" PRIx64 " ns=%" PRIu64 "\n",
                output.size(), hash, elapsed);
}
#endif
}

#if defined(BENCH_EXECUTION_MATRIX)
int main()
{
    bench_report_mode();
    run();
}
#elif defined(__wasi__)
extern "C" void _start() { run(); }
#else
int main() { run(); }
#endif
