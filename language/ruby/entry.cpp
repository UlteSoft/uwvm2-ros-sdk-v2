/**
 * @file entry.cpp
 * @brief Execute one embedded Ruby program in the target's mruby interpreter.
 */
#include <mruby.h>
#include <mruby/array.h>
#include <mruby/compile.h>
#include <mruby/data.h>
#include <mruby/error.h>
#include <mruby/string.h>

#include <wros/scene.h>
#include <cstdlib>
#include <cstring>

#include "application.inc"
#include "mrblib.inc"

namespace
{
using operation = uint32_t (*)(uint64_t, uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);

struct method
{
    const char *name;
    operation invoke;
    bool report;
};
#include "operations.inc"

#if defined(WROS_RUBY_OPEN) || defined(WROS_RUBY_CLOSE) || defined(WROS_RUBY_CALL)
/** @brief Clear call-owned memory before making it available to the allocator. */
void erase(void *data, size_t size)
{
    auto *bytes = static_cast<volatile unsigned char *>(data);
    for (size_t index = 0; index < size; ++index) bytes[index] = 0;
}

/** @brief Store the token in typed Ruby data without granting disposal effects. */
struct handle
{
    uint64_t token;
    bool live;
};

/** @brief Wipe a retired local token without initiating any host operation. */
void release_handle(mrb_state *mrb, void *data)
{
    if (data)
    {
        erase(data, sizeof(handle));
        mrb_free(mrb, data);
    }
}

const mrb_data_type handle_type = {"WROS::Capability", release_handle};

#if defined(WROS_RUBY_CLOSE) || defined(WROS_RUBY_CALL)
/** @brief Resolve a typed, locally live token before invoking an authorized import. */
handle *checked_handle(mrb_state *mrb, mrb_value instance)
{
    auto *value = static_cast<handle *>(mrb_data_get_ptr(mrb, instance, &handle_type));
    if (!value || !value->live) mrb_raise(mrb, E_ARGUMENT_ERROR, "expected a live WROS capability");
    return value;
}
#endif

#if defined(WROS_RUBY_OPEN)
/** @brief Return the host status and an opaque capability for one declared alias. */
mrb_value open_alias(mrb_state *mrb, mrb_value self)
{
    mrb_value alias;
    mrb_get_args(mrb, "S", &alias);
    if (RSTRING_LEN(alias) > 4096) mrb_raise(mrb, E_ARGUMENT_ERROR, "capability alias exceeds 4096 bytes");
    auto *kind = mrb_class_get_under(mrb, mrb_class_ptr(self), "Capability");
    auto *data = mrb_data_object_alloc(mrb, kind, nullptr, &handle_type);
    auto result = mrb_ary_new_capa(mrb, 2);
    auto *value = static_cast<handle *>(mrb_malloc(mrb, sizeof(handle)));
    *value = {0, false};
    data->data = value;
    auto status = wr_capability_open(0, reinterpret_cast<uintptr_t>(RSTRING_PTR(alias)),
        static_cast<uint64_t>(RSTRING_LEN(alias)), reinterpret_cast<uintptr_t>(&value->token));
    value->live = status == 0;
    mrb_value fields[] = {mrb_int_value(mrb, status), value->live ? mrb_obj_value(data) : mrb_nil_value()};
    for (auto item : fields) mrb_ary_push(mrb, result, item);
    return result;
}
#endif

#ifdef WROS_RUBY_CLOSE
/** @brief Invoke the explicitly imported close operation and retire the local token. */
mrb_value close_alias(mrb_state *mrb, mrb_value)
{
    mrb_value instance;
    mrb_get_args(mrb, "o", &instance);
    auto *value = checked_handle(mrb, instance);
    auto status = wr_capability_close(value->token);
    if (!status) *value = {0, false};
    return mrb_int_value(mrb, status);
}
#endif
#endif

#ifdef WROS_RUBY_ABI
/** @brief Fetch the exposed ROSv2 ABI version. */
mrb_value abi(mrb_state *mrb, mrb_value)
{
    return mrb_int_value(mrb, wr_abi());
}
#endif

#ifdef WROS_RUBY_CALL
/** @brief Own and wipe a temporary host exchange buffer, including on Ruby exceptions. */
struct exchange_buffer
{
    size_t size;
    char *data;
    explicit exchange_buffer(size_t count)
        : size(count), data(count ? static_cast<char *>(std::calloc(count, 1)) : nullptr)
    {}
    ~exchange_buffer()
    {
        if (data) erase(data, size);
        std::free(data);
    }
    exchange_buffer(const exchange_buffer &) = delete;
    exchange_buffer &operator=(const exchange_buffer &) = delete;
};

/** @brief Invoke an exact preselected ROSv2 operation over bounded guest memory. */
mrb_value call(mrb_state *mrb, mrb_value)
{
    mrb_value name, instance, request;
    mrb_int capacity;
    mrb_get_args(mrb, "SoSi", &name, &instance, &request, &capacity);
    const char *label = RSTRING_PTR(name);
    auto label_size = static_cast<size_t>(RSTRING_LEN(name));
    const method *entry = methods;
    while (entry->name)
    {
        if (std::strlen(entry->name) == label_size && !std::memcmp(entry->name, label, label_size)) break;
        ++entry;
    }
    if (!entry->name) mrb_raise(mrb, E_ARGUMENT_ERROR, "ROS operation was not included in this program");
    uint64_t token = mrb_nil_p(instance) ? 0 : checked_handle(mrb, instance)->token;
    constexpr auto limit = 4 * 1024 * 1024;
    auto length = RSTRING_LEN(request);
    if (capacity < 0 || capacity > limit || length > limit) mrb_raise(mrb, E_ARGUMENT_ERROR, "ROS buffer exceeds 4 MiB");
    exchange_buffer input(static_cast<size_t>(length)), output(static_cast<size_t>(capacity));
    if ((length && !input.data) || (capacity && !output.data)) mrb_raise(mrb, E_RUNTIME_ERROR, "exchange allocation failed");
    if (length) std::memcpy(input.data, RSTRING_PTR(request), input.size);
    uint64_t bytes = 0;
    uint32_t status = entry->invoke(token, 0, reinterpret_cast<uintptr_t>(input.data), input.size,
        reinterpret_cast<uintptr_t>(output.data), output.size, reinterpret_cast<uintptr_t>(&bytes));
    auto payload = mrb_nil_value();
    if (!status || (entry->report && status == 95 && bytes))
    {
        if (bytes > output.size) mrb_raise(mrb, E_RUNTIME_ERROR, "invalid ROS reply size");
        payload = mrb_str_new(mrb, output.data ? output.data : "", static_cast<size_t>(bytes));
    }
    if (bytes > static_cast<uint64_t>(MRB_INT_MAX)) mrb_raise(mrb, E_RUNTIME_ERROR, "unrepresentable ROS reply size");
    mrb_value fields[] = {mrb_int_value(mrb, status), payload, mrb_int_value(mrb, static_cast<mrb_int>(bytes))};
    return mrb_ary_new_from_values(mrb, 3, fields);
}
#endif

/** @brief Install only linked Ruby bindings and evaluate counted source inside the guest. */
mrb_value run(mrb_state *mrb, void *)
{
    auto *module = mrb_define_module(mrb, "WROS");
#ifdef WROS_RUBY_ABI
    mrb_define_module_function(mrb, module, "abi", abi, MRB_ARGS_NONE());
#endif
#ifdef WROS_RUBY_OPEN
    mrb_define_class_under(mrb, module, "Capability", mrb->object_class);
    mrb_define_module_function(mrb, module, "open", open_alias, MRB_ARGS_REQ(1));
#endif
#ifdef WROS_RUBY_CLOSE
    mrb_define_module_function(mrb, module, "close", close_alias, MRB_ARGS_REQ(1));
#endif
#ifdef WROS_RUBY_CALL
    mrb_define_module_function(mrb, module, "call", call, MRB_ARGS_REQ(4));
#endif
    return mrb_load_nstring(mrb, application, sizeof(application) - 1);
}
}

/** @brief Bootstrap the upstream Ruby core class library inside the interpreter. */
void mrb_init_mrblib(mrb_state *mrb)
{
    mrb_load_nstring(mrb, mrblib, sizeof(mrblib) - 1);
    if (mrb->exc) mrb_exc_raise(mrb, mrb_obj_value(mrb->exc));
}

/** @brief Run the application once and trap after an uncaught Ruby error. */
extern "C" void _start()
{
    auto *mrb = mrb_open_core();
    if (!mrb) __builtin_trap();
    mrb_bool failed = mrb->exc != nullptr;
    if (!failed) mrb_protect_error(mrb,run,nullptr,&failed);
    failed = failed || mrb->exc;
    mrb_close(mrb);
    if (failed) __builtin_trap();
}
