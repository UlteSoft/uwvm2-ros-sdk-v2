// Build against the pinned Wasmtime 42.0.1 C API. Reuse the qualification
// adapter's memory, WASIp1 permissions, output, trap and clock handling.
#include <wasmtime.h>
#include <cstdio>
#include <stdexcept>

static wasm_engine_t *execution_engine(wasm_config_t *config)
{
#if defined(__x86_64__)
    constexpr auto target = "x86_64-unknown-linux-gnu";
#elif defined(__aarch64__)
    constexpr auto target = "aarch64-unknown-linux-gnu";
#else
#error "Build the ordinary wasmtime_reference host for 32-bit correctness probes"
#endif
    wasmtime_config_strategy_set(config, WASMTIME_STRATEGY_CRANELIFT);
    wasmtime_config_cranelift_opt_level_set(config, WASMTIME_OPT_LEVEL_SPEED);
    if (auto *error = wasmtime_config_target_set(config, target)) {
        wasmtime_error_delete(error);
        wasm_config_delete(config);
        throw std::runtime_error("native Cranelift target unavailable");
    }
    auto *engine = wasm_engine_new_with_config(config);
    if (engine)
        std::fprintf(stderr, "execution-matrix native-cranelift %s\n", target);
    return engine;
}

#define wasm_engine_new_with_config execution_engine
#include "../wasmtime_reference/host.cpp"
