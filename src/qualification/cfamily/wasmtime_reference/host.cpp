// Qualification host for the external C/C++ corpus. Build with the v42.0.1 C API.
#include <wasmtime.h>

#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#include <sched.h>
#include <time.h>
#include <unistd.h>

static_assert(WASMTIME_VERSION_MAJOR == 42 && WASMTIME_VERSION_MINOR == 0 &&
              WASMTIME_VERSION_PATCH == 1, "use the pinned Wasmtime C API");

using std::string_view;

enum Errno { success = 0, bad_fd = 8, fault = 21, invalid = 28, io = 29,
             overflow = 61, not_capable = 76 };
enum class Operation { args, args_sizes, clock, environ, environ_sizes, fdstat, write, exit, yield, denied };

struct Function {
    string_view name;
    Operation operation;
    // i = i32, l = i64, p = target pointer/size. Only proc_exit has no result.
    string_view parameters;
};
constexpr Function functions[] = {
    {"args_get", Operation::args, "pp"},
    {"args_sizes_get", Operation::args_sizes, "pp"},
    {"clock_time_get", Operation::clock, "ilp"},
    {"environ_get", Operation::environ, "pp"},
    {"environ_sizes_get", Operation::environ_sizes, "pp"},
    {"fd_fdstat_get", Operation::fdstat, "ip"},
    {"fd_write", Operation::write, "ippp"},
    {"proc_exit", Operation::exit, "i"},
    {"sched_yield", Operation::yield, ""},
    {"poll_oneoff", Operation::denied, "pppp"},
    {"fd_close", Operation::denied, "i"},
    {"fd_prestat_dir_name", Operation::denied, "ipp"},
    {"fd_prestat_get", Operation::denied, "ip"},
    {"fd_read", Operation::denied, "ippp"},
    {"fd_seek", Operation::denied, "ilip"},
};

struct Host {
    unsigned width;
    FILE *report;
    std::set<string_view> grants;
    std::map<string_view, bool> interfaces;
    string_view guest_argv0;
    wasmtime_sharedmemory_t *shared = nullptr;
    bool exited = false;
    uint32_t exit_code = 0;

    bool has(string_view grant) const { return grants.count(grant) != 0; }
    bool writable(uint32_t fd) const {
        return (fd == 1 && has("stdout.write")) || (fd == 2 && has("stderr.write"));
    }
};

struct Binding {
    Host &host;
    const Function &function;
    bool allowed;
};

struct Memory {
    uint8_t *data = nullptr;
    size_t size = 0;

    bool contains(uint64_t address, uint64_t length) const {
        return data && address <= size && length <= size - address;
    }
    uint64_t load(uint64_t address, unsigned bytes) const {
        uint64_t value = 0;
        for (unsigned i = 0; i < bytes; ++i)
            value |= uint64_t(data[address + i]) << (8 * i);
        return value;
    }
    void store(uint64_t address, unsigned bytes, uint64_t value) const {
        for (unsigned i = 0; i < bytes; ++i)
            data[address + i] = uint8_t(value >> (8 * i));
    }
};

// No thread-spawn import is admitted. Wasm is suspended for the entire host call.
// Resolve the current size on each call to account for intervening memory.grow.
static Memory guest_memory(const Host &host, wasmtime_caller_t *caller) {
    if (host.shared)
        return {wasmtime_sharedmemory_data(host.shared), wasmtime_sharedmemory_data_size(host.shared)};
    wasmtime_extern_t item;
    if (!wasmtime_caller_export_get(caller, "memory", 6, &item))
        return {};
    Memory memory;
    if (item.kind == WASMTIME_EXTERN_MEMORY) {
        auto *context = wasmtime_caller_context(caller);
        memory = {wasmtime_memory_data(context, &item.of.memory),
                  wasmtime_memory_data_size(context, &item.of.memory)};
    }
    wasmtime_extern_delete(&item);
    return memory;
}

static Errno fd_write(const Host &host, Memory memory, uint32_t fd, uint64_t iovs,
                      uint64_t count, uint64_t nwritten) {
    const unsigned width = host.width;
    if (fd <= 2 && !host.writable(fd)) return not_capable;
    if (!memory.contains(nwritten, width)) return fault;
    if (nwritten % width || iovs % width) return invalid;
    if (fd > 2) return bad_fd;
    const unsigned stride = 2 * width;
    if (count > UINT64_MAX / stride) return overflow;
    if (!memory.contains(iovs, count * stride)) return fault;
    const uint64_t max_size = width == 4 ? UINT32_MAX : UINT64_MAX;
    uint64_t total = 0;
    for (uint64_t i = 0; i < count; ++i) {
        const auto entry = iovs + i * stride;
        const auto buffer = memory.load(entry, width);
        const auto length = memory.load(entry + width, width);
        if (!memory.contains(buffer, length)) return fault;
        if (length > max_size - total) return overflow;
        total += length;
    }
    // Validate the complete scatter list before publishing any output. No guest
    // code runs between these passes. Leave the result cell untouched on error.
    uint64_t written = 0;
    for (uint64_t i = 0; i < count; ++i) {
        const auto entry = iovs + i * stride;
        auto buffer = memory.load(entry, width);
        auto length = memory.load(entry + width, width);
        while (length) {
            auto bytes = ::write(static_cast<int>(fd), memory.data + buffer,
                                 std::min<uint64_t>(length, SSIZE_MAX));
            if (bytes < 0 && errno == EINTR) continue;
            if (bytes <= 0) {
                if (written == 0) return io;
                memory.store(nwritten, width, written);
                return success;
            }
            written += bytes;
            buffer += bytes;
            length -= bytes;
        }
    }
    memory.store(nwritten, width, written);
    return success;
}

static uint64_t integer(const wasmtime_val_t &arg) {
    return arg.kind == WASMTIME_I32 ? uint32_t(arg.of.i32) : uint64_t(arg.of.i64);
}

static Errno store_sizes(Memory memory, unsigned width, uint64_t count_ptr, uint64_t bytes_ptr,
                         uint64_t count, uint64_t bytes) {
    if (!memory.contains(count_ptr, width) || !memory.contains(bytes_ptr, width)) return fault;
    if (count_ptr % width || bytes_ptr % width) return invalid;
    memory.store(count_ptr, width, count);
    memory.store(bytes_ptr, width, bytes);
    return success;
}

static Errno hostcall(const Binding &binding, wasmtime_caller_t *caller,
                      const wasmtime_val_t *args) {
    auto &host = binding.host;
    if (!binding.allowed) return not_capable;
    const auto op = binding.function.operation;
    if ((op == Operation::args || op == Operation::args_sizes) && !host.has("args")) return not_capable;
    if (op == Operation::yield) {
        if (!host.has("sched-yield")) return not_capable;
        return sched_yield() == 0 ? success : io;
    }
    const auto memory = guest_memory(host, caller);
    const auto a = integer(args[0]);
    const auto b = integer(args[1]);
    switch (op) {
    case Operation::args:
        if (!memory.data) return fault;
        if (a % host.width) return invalid;
        if (!memory.contains(a, host.width) || !memory.contains(b, host.guest_argv0.size() + 1)) return fault;
        // The producer passes one argument. WASIp1 owns exactly one pointer slot.
        memory.store(a, host.width, b);
        std::memcpy(memory.data + b, host.guest_argv0.data(), host.guest_argv0.size());
        memory.data[b + host.guest_argv0.size()] = 0;
        return success;
    case Operation::args_sizes:
        return store_sizes(memory, host.width, a, b, 1, host.guest_argv0.size() + 1);
    case Operation::clock: {
        const auto result = integer(args[2]);
        if (!memory.contains(result, 8)) return fault;
        if (result % 8 || a > 3) return invalid;
        if (a != 1 || !host.has("monotonic-clock")) return not_capable;
        timespec ts;
        if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return io;
        uint64_t ns = uint64_t(ts.tv_sec) * 1000000000 + ts.tv_nsec;
        memory.store(result, 8, ns);
        std::fprintf(host.report, "clock_monotonic_ns %llu\n", static_cast<unsigned long long>(ns));
        return success;
    }
    case Operation::environ:
        if (!host.has("environ")) return not_capable;
        return memory.contains(a, 0) && memory.contains(b, 0) ? success : fault;
    case Operation::environ_sizes:
        if (!host.has("environ")) return not_capable;
        return store_sizes(memory, host.width, a, b, 0, 0);
    case Operation::fdstat:
        if (a <= 2 && (!host.writable(a) || !host.has("stdio.metadata"))) return not_capable;
        if (!memory.contains(b, 24)) return fault;
        if (b % 8) return invalid;
        if (a > 2) return bad_fd;
        // Captures are regular output files. Preview1 fdstat is 24 bytes at both widths.
        std::memset(memory.data + b, 0, 24);
        memory.data[b] = 4; // regular file
        memory.store(b + 8, 8, (1u << 6) | (1u << 21)); // FD_WRITE | FD_FILESTAT_GET
        return success;
    case Operation::write:
        return fd_write(host, memory, a, b, integer(args[2]), integer(args[3]));
    default:
        std::abort(); // checked on import, proc_exit is handled in callback
    }
}

static wasm_trap_t *callback(void *data, wasmtime_caller_t *caller, const wasmtime_val_t *args,
                             size_t, wasmtime_val_t *results, size_t) {
    const auto &binding = *static_cast<Binding *>(data);
    auto &host = binding.host;
    const auto name = binding.function.name;
    if (binding.function.operation == Operation::exit) {
        if (!binding.allowed || !host.has("proc-exit")) {
            constexpr char msg[] = "denied proc_exit";
            std::fprintf(host.report, "call proc_exit denied\n");
            return wasmtime_trap_new(msg, sizeof(msg) - 1);
        }
        host.exited = true;
        host.exit_code = uint32_t(integer(args[0]));
        std::fprintf(host.report, "call proc_exit %u\n", host.exit_code);
        constexpr char msg[] = "qualification proc_exit";
        return wasmtime_trap_new(msg, sizeof(msg) - 1);
    }
    auto result = hostcall(binding, caller, args);
    std::fprintf(host.report, "call %.*s %u\n", int(name.size()), name.data(), unsigned(result));
    results[0].kind = WASMTIME_I32;
    results[0].of.i32 = result;
    return nullptr;
}

static std::string name_of(const wasm_name_t *name) { return {name->data, name->size}; }

static const Function &function_for(const std::string &name, unsigned width) {
    for (const auto &function : functions) {
        std::string expected(function.name);
        if (width == 8) expected += "_wasm64";
        if (expected == name) return function;
    }
    throw std::runtime_error("unsupported WASIp1 import " + name);
}

static void check_signature(const wasm_functype_t *type, const Function &function, unsigned width) {
    if (!type) throw std::runtime_error("expected a function import");
    const auto *params = wasm_functype_params(type);
    const auto *results = wasm_functype_results(type);
    bool valid = params->size == function.parameters.size() &&
                 results->size == (function.operation == Operation::exit ? 0u : 1u);
    for (size_t i = 0; valid && i < params->size; ++i) {
        auto p = function.parameters[i];
        auto kind = p == 'l' || (p == 'p' && width == 8) ? WASM_I64 : WASM_I32;
        valid = wasm_valtype_kind(params->data[i]) == kind;
    }
    if (!valid || (results->size && wasm_valtype_kind(results->data[0]) != WASM_I32))
        throw std::runtime_error("signature mismatch for " + std::string(function.name));
}

static void check(wasmtime_error_t *error, wasm_trap_t *trap = nullptr) {
    if (!error && !trap) return;
    wasm_name_t message;
    if (error) {
        wasmtime_error_message(error, &message);
        wasmtime_error_delete(error);
    } else {
        wasm_trap_message(trap, &message);
    }
    if (trap) wasm_trap_delete(trap);
    auto detail = name_of(&message);
    wasm_name_delete(&message);
    throw std::runtime_error(detail);
}

static wasmtime_module_t *compile(wasm_engine_t *engine, const char *path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("could not open " + std::string(path));
    std::vector<uint8_t> bytes(std::istreambuf_iterator<char>{file}, {});
    wasmtime_module_t *module;
    check(wasmtime_module_new(engine, bytes.data(), bytes.size(), &module));
    return module;
}

static void memory_type(const wasm_memorytype_t *type, unsigned width, bool shared) {
    if (!type || wasmtime_memorytype_is64(type) != (width == 8) ||
        wasmtime_memorytype_isshared(type) != shared || wasmtime_memorytype_page_size(type) != 65536)
        throw std::runtime_error("memory type disagrees with profile");
}

static void run(Host &host, bool eh, const char *guest, const char *owner) {
    // Each process owns one store, one guest and at most one owner, for one execution only.
    bool shared = string_view(owner) != "-";
    auto *config = wasm_config_new();
    wasmtime_config_wasm_memory64_set(config, host.width == 8);
    wasmtime_config_wasm_threads_set(config, shared);
    wasmtime_config_shared_memory_set(config, shared);
    wasmtime_config_wasm_exceptions_set(config, eh);
    wasmtime_config_parallel_compilation_set(config, false);
    auto *engine = wasm_engine_new_with_config(config);
    if (!engine) throw std::runtime_error("Wasmtime engine configuration rejected");
    auto *store = wasmtime_store_new(engine, nullptr, nullptr);
    auto *context = wasmtime_store_context(store);
    auto *module = compile(engine, guest);
    wasm_trap_t *trap = nullptr;
    wasmtime_extern_t owned_memory{};
    if (shared) {
        auto *owner_module = compile(engine, owner);
        wasmtime_instance_t owner_instance;
        auto *error = wasmtime_instance_new(context, owner_module, nullptr, 0, &owner_instance, &trap);
        check(error, trap);
        if (!wasmtime_instance_export_get(context, &owner_instance, "memory", 6, &owned_memory) ||
            owned_memory.kind != WASMTIME_EXTERN_SHAREDMEMORY)
            throw std::runtime_error("owner must export shared memory");
        host.shared = owned_memory.of.sharedmemory;
        auto *type = wasmtime_sharedmemory_type(host.shared);
        memory_type(type, host.width, true);
        wasm_memorytype_delete(type);
        wasmtime_module_delete(owner_module);
    }

    wasm_importtype_vec_t requirements;
    wasmtime_module_imports(module, &requirements);
    std::vector<wasmtime_extern_t> imports(requirements.size);
    std::vector<Binding> bindings;
    bindings.reserve(requirements.size); // callback addresses stay valid until _start returns
    std::set<std::string> used;
    bool bound_owner = false;
    for (size_t i = 0; i < requirements.size; ++i) {
        const auto *item = requirements.data[i];
        auto module_name = name_of(wasm_importtype_module(item));
        auto name = name_of(wasm_importtype_name(item));
        auto *type = wasm_importtype_type(item);
        if (module_name == "env" && name == "memory" && shared && !bound_owner) {
            memory_type(wasm_externtype_as_memorytype_const(type), host.width, true);
            imports[i] = owned_memory; // wasmtime_instance_new clones this same memory handle
            bound_owner = true;
            continue;
        }
        if (module_name != "wasi_snapshot_preview1")
            throw std::runtime_error("unexpected import " + module_name + "." + name);
        auto mode = host.interfaces.find(name);
        if (mode == host.interfaces.end() || !used.insert(name).second)
            throw std::runtime_error("missing or ambiguous interface policy for " + name);
        const auto &function = function_for(name, host.width);
        if (function.operation == Operation::denied && mode->second)
            throw std::runtime_error("only the denied profile is implemented for " + name);
        auto *func_type = wasm_externtype_as_functype_const(type);
        check_signature(func_type, function, host.width);
        auto &binding = bindings.emplace_back(Binding{host, function, mode->second});
        imports[i].kind = WASMTIME_EXTERN_FUNC;
        wasmtime_func_new(context, func_type, callback, &binding, nullptr, &imports[i].of.func);
    }
    if (bound_owner != shared || used.size() != host.interfaces.size())
        throw std::runtime_error("actual imports disagree with recorded interfaces or memory owner");
    wasm_importtype_vec_delete(&requirements);
    std::fprintf(host.report, "memory %s\n", shared ? "env.memory" : "caller.memory");
    wasmtime_instance_t instance;
    auto *error = wasmtime_instance_new(context, module, imports.data(), imports.size(), &instance, &trap);
    check(error, trap);
    if (!shared) {
        wasmtime_extern_t memory;
        if (!wasmtime_instance_export_get(context, &instance, "memory", 6, &memory) ||
            memory.kind != WASMTIME_EXTERN_MEMORY)
            throw std::runtime_error("private guest must export memory");
        auto *type = wasmtime_memory_type(context, &memory.of.memory);
        memory_type(type, host.width, false);
        wasm_memorytype_delete(type);
        wasmtime_extern_delete(&memory);
    }
    wasmtime_extern_t start;
    if (!wasmtime_instance_export_get(context, &instance, "_start", 6, &start) ||
        start.kind != WASMTIME_EXTERN_FUNC)
        throw std::runtime_error("missing _start function");
    std::fputs("invoke _start\n", host.report);
    error = wasmtime_func_call(context, &start.of.func, nullptr, 0, nullptr, 0, &trap);
    if (host.exited && (error || trap)) {
        if (error) wasmtime_error_delete(error);
        if (trap) wasm_trap_delete(trap);
        std::fprintf(host.report, "end proc_exit %u\n", host.exit_code);
    } else {
        check(error, trap);
        std::fputs("end returned 0\n", host.report);
    }
    wasmtime_extern_delete(&start);
    if (shared) wasmtime_extern_delete(&owned_memory);
    wasmtime_module_delete(module);
    wasmtime_store_delete(store);
    wasm_engine_delete(engine);
}

int main(int argc, char **argv) {
    if (argc < 6) {
        std::fputs("usage: host 32|64 eh|noeh GUEST OWNER|- REPORT [allow=IMPORT|deny=IMPORT|grant=NAME|guest-argv0=PATH ...]\n", stderr);
        return 2;
    }
    auto *report = std::fopen(argv[5], "wx");
    if (!report) return 2;
    std::setvbuf(report, nullptr, _IOLBF, 0);
    try {
        string_view bits(argv[1]), eh(argv[2]);
        if ((bits != "32" && bits != "64") || (eh != "eh" && eh != "noeh"))
            throw std::runtime_error("invalid profile");
        Host host{bits == "64" ? 8u : 4u, report, {}, {}, {}};
        for (int i = 6; i < argc; ++i) {
            string_view option(argv[i]);
            auto pos = option.find('=');
            if (pos == option.npos) throw std::runtime_error("bad policy option");
            auto key = option.substr(0, pos), value = option.substr(pos + 1);
            if (key == "grant") {
                static const std::set<string_view> supported{
                    "args", "environ", "monotonic-clock", "proc-exit", "sched-yield", "stderr.write", "stdio.metadata", "stdout.write"};
                if (!supported.count(value) || !host.grants.insert(value).second)
                    throw std::runtime_error("unknown or duplicate grant");
            } else if (key == "guest-argv0") {
                if (!host.guest_argv0.empty() || value.empty() || value.front() != '/')
                    throw std::runtime_error("expected one absolute producer guest path");
                host.guest_argv0 = value;
            } else if ((key != "allow" && key != "deny") ||
                       !host.interfaces.emplace(value, key == "allow").second) {
                throw std::runtime_error("unknown or duplicate interface option");
            }
        }
        if (host.has("args") != !host.guest_argv0.empty())
            throw std::runtime_error("the args grant and recorded guest-argv0 must be supplied together");
        std::fputs("wasmtime-c-api " WASMTIME_VERSION "\n", report);
        run(host, eh == "eh", argv[3], argv[4]);
    } catch (const std::exception &error) {
        std::fprintf(report, "error %s\n", error.what());
        std::fclose(report);
        return 1;
    }
    return std::fclose(report) == 0 ? 0 : 1;
}
