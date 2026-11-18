/** @file entry.cpp
 * @brief Run an embedded text chunk in a fresh Lua state inside the guest.
 * @details Only pure libraries are registered. If selected at build time, the
 * ROS ABI inquiry also needs exposure to this module under the VM's policy.
 * Lua errors close the state before trapping. Execution time and total Wasm
 * memory, including allocations outside the Lua heap, are deployment limits.
 */
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
#include <cstdlib>
#include "chunk.inc"
#ifdef WROS_LUA_GUEST_CLOCKLESS
#include <cerrno>
#include <ctime>

// The single-threaded wasi-libc futex fallback can consult absolute time when
// given a deadline. No Lua library exposes timed waits in this profile. Make
// such a request return an explicit error without acquiring a clock import.
extern "C" int __clock_gettime(clockid_t, struct timespec *) {
    errno = ENOTSUP;
    return -1;
}
#endif
#ifdef WROS_LUA_SCENE
#include "scene.hpp"
#endif

static void *allocate(void *context, void *pointer, size_t old_size, size_t size) {
    auto &used = *static_cast<size_t *>(context);
    constexpr size_t maximum = 16 * 1024 * 1024;
    // For a new object Lua supplies a type tag in old_size.
    const size_t retained = used - (pointer ? old_size : 0);
    if (!size) {
        std::free(pointer);
        used = retained;
        return nullptr;
    }
    if (size > maximum - retained) return nullptr;
    void *next = std::realloc(pointer, size);
    if (next) used = retained + size;
    return next;
}

static int run(lua_State *state) {
    const luaL_Reg libraries[] = {
        {"_G", luaopen_base}, {"table", luaopen_table}, {"string", luaopen_string},
        {"math", luaopen_math}, {"utf8", luaopen_utf8}, {"coroutine", luaopen_coroutine}
    };
    for (const auto &library : libraries) {
        luaL_requiref(state, library.name, library.func, 1);
        lua_pop(state, 1);
    }
#ifdef WROS_LUA_SCENE
    wros_lua::install(state);
#endif
    if (luaL_loadbufferx(state, script, sizeof(script) - 1, "=application", "t") != LUA_OK)
        return lua_error(state);
    lua_call(state, 0, 0);
    return 0;
}

extern "C" void _start() {
    size_t used = 0;
    lua_State *state = lua_newstate(allocate, &used);
    if (!state) __builtin_trap();
    lua_pushcfunction(state, run);
    int status = lua_pcall(state, 0, 0, 0);
    lua_close(state);
    if (status != LUA_OK) __builtin_trap();
}
