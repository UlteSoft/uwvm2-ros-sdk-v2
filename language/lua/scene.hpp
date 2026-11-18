/** @file scene.hpp
 * @brief Marshal the selected ROSv2 imports between a Lua script and its VM scene.
 * @details Each compiled guest imports only operations selected by its developer.
 * The VM checks the current module, capability, deployment policy and wire schema.
 * Lua never supplies a linear-memory address. Requests are copied into private
 * scratch because an authorized VM operation may consume and clear its input.
 */
#pragma once
#include <cstdint>
#include <cstring>
#include <limits>
#include <wros/scene.h>

namespace wros_lua {
inline constexpr char handle_type[] = "wros.capability";
struct handle { std::uint64_t token; bool closed; };
inline std::uint64_t address(const void *p) { return reinterpret_cast<std::uintptr_t>(p); }

inline void erase(void *data, size_t n) {
    auto *p = static_cast<volatile unsigned char *>(data);
    while (n--) *p++ = 0;
}

inline int abi(lua_State *s) {
    lua_pushinteger(s, wr_abi());
    return 1;
}

inline int open(lua_State *s) {
    size_t n{};
    luaL_checktype(s, 1, LUA_TSTRING);
    const char *alias = lua_tolstring(s, 1, &n);
    auto *value = static_cast<handle *>(lua_newuserdatauv(s, sizeof(handle), 0));
    value->token = 0;
    value->closed = true;
    luaL_setmetatable(s, handle_type);
    auto status = wr_capability_open(0, address(alias), n, address(&value->token));
    if (status) {
        value->token = 0;
        lua_pop(s, 1);
        lua_pushnil(s);
    } else {
        value->closed = false;
    }
    lua_pushinteger(s, status);
    lua_insert(s, -2);
    return 2;
}

inline handle *checked(lua_State *s) {
    auto *value = static_cast<handle *>(luaL_checkudata(s, 1, handle_type));
    luaL_argcheck(s, !value->closed, 1, "closed capability");
    return value;
}

inline int close(lua_State *s) {
    auto *value = checked(s);
    auto status = wr_capability_close(value->token);
    if (!status) {
        value->token = 0;
        value->closed = true;
    }
    lua_pushinteger(s, status);
    return 1;
}

inline int copy_reply(lua_State *s) {
    const char *data = static_cast<const char *>(lua_touserdata(s, 1));
    lua_pushlstring(s, data, static_cast<size_t>(lua_tointeger(s, 2)));
    return 1;
}

using operation = std::uint32_t(std::uint64_t, std::uint32_t, std::uint64_t, std::uint64_t,
                                std::uint64_t, std::uint64_t, std::uint64_t);

template<operation &invoke, bool permission_report = false>
int call(lua_State *s) {
    // Some introspection operations use token zero. Only the VM decides whether it is authorized.
    auto token = lua_isnil(s, 1) ? 0 : checked(s)->token;
    size_t n{};
    luaL_checktype(s, 2, LUA_TSTRING);
    const char *request = lua_tolstring(s, 2, &n);
    auto capacity = luaL_checkinteger(s, 3);
    constexpr size_t heap_limit = 16u * 1024u * 1024u;
    luaL_argcheck(s, n <= heap_limit, 2, "request exceeds the Lua heap limit");
    luaL_argcheck(s, capacity >= 0 && static_cast<lua_Unsigned>(capacity) <= heap_limit,
                  3, "response exceeds the Lua heap limit");
    luaL_checkstack(s, 10, "ROS response");
    auto *input = lua_newuserdatauv(s, n, 0);
    auto *output = lua_newuserdatauv(s, static_cast<size_t>(capacity), 0);
    if (n) std::memcpy(input, request, n);
    if (capacity) std::memset(output, 0, static_cast<size_t>(capacity));
    std::uint64_t written{};
    auto status = invoke(token, 0, n ? address(input) : 0, n, capacity ? address(output) : 0,
                         static_cast<std::uint64_t>(capacity), address(&written));
    erase(input, n);
    int copy_status = LUA_OK;
    lua_pushinteger(s, status);
    // A whole uncompiled family returns ENOTSUP with a nonempty report. An
    // unknown exact function returns the same status without writing the length.
    bool has_reply = !status || (permission_report && status == 95 && written != 0);
    if (has_reply && written <= static_cast<std::uint64_t>(capacity)) {
        lua_pushcfunction(s, copy_reply);
        lua_pushlightuserdata(s, output);
        lua_pushinteger(s, static_cast<lua_Integer>(written));
        copy_status = lua_pcall(s, 2, 1, 0);
    } else {
        lua_pushnil(s);
    }
    erase(output, static_cast<size_t>(capacity));
    if (copy_status != LUA_OK) return lua_error(s);
    if ((has_reply && written > static_cast<std::uint64_t>(capacity)) ||
        written > static_cast<std::uint64_t>(std::numeric_limits<lua_Integer>::max()))
        return luaL_error(s, "invalid ROS reply length");
    lua_pushinteger(s, static_cast<lua_Integer>(written));
    return 3;
}

inline void install(lua_State *s) {
    if (luaL_newmetatable(s, handle_type)) {
        lua_pushliteral(s, "ROS capability");
        lua_setfield(s, -2, "__metatable");
    }
    lua_pop(s, 1);
    static const luaL_Reg methods[] = {
#include "scene_methods.inc"
        {nullptr, nullptr}
    };
    luaL_newlib(s, methods);
    lua_setglobal(s, "wros");
}
}
