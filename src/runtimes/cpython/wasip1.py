"""Limit guest libc imports to the CPython command, clocks, console and read-only script inputs."""
import re

# Each entry is the actual core Wasm32 Preview1 function type.
P = "i32"
Q = "i64"
SIGNATURES = {
    "args_get": [P, P], "args_sizes_get": [P, P],
    "clock_res_get": [P, P], "clock_time_get": [P, Q, P],
    "fd_fdstat_get": [P, P], "fd_filestat_get": [P, P], "fd_write": [P, P, P, P],
    "fd_read": [P, P, P, P], "fd_close": [P], "fd_seek": [P, Q, P, P], "fd_tell": [P, P],
    "fd_readdir": [P, P, P, Q, P],
    "fd_prestat_get": [P, P], "fd_prestat_dir_name": [P, P, P],
    "path_open": [P, P, P, P, P, Q, Q, P, P], "path_filestat_get": [P, P, P, P, P],
    "proc_exit": [P],
}
SHARED_ONLY = {"fd_prestat_get", "fd_prestat_dir_name", "path_open", "path_filestat_get", "fd_readdir"}


def allowed(shared):
    return set(SIGNATURES) if shared else set(SIGNATURES) - SHARED_ONLY


def declarations(header, shared):
    """Return type-correct local denials for libc operations outside this runtime ABI."""
    text = re.sub(r"/\*.*?\*/", "", header.read_text(), flags=re.S)
    pattern = r"\b__wasi_errno_t\s+(__wasi_[a-z0-9_]+)\s*(\([^()]*\))\s*__attribute__\(\(__warn_unused_result__\)\);"
    prototypes = dict(re.findall(pattern, text))
    permitted = allowed(shared)
    required = {"__wasi_" + name for name in SIGNATURES if name != "proc_exit"}
    if not required <= prototypes.keys():
        raise ValueError("unexpected WASI libc declarations")
    lines, wrapped = ["#include <wasi/api.h>"], []
    for symbol, args in sorted(prototypes.items()):
        name = symbol.removeprefix("__wasi_")
        if name in permitted:
            continue
        if name == "environ_sizes_get":
            body = "*retptr0 = 0; *retptr1 = 0; return __WASI_ERRNO_SUCCESS;"
        elif name == "environ_get":
            body = "return __WASI_ERRNO_SUCCESS;"
        else:
            code = "__WASI_ERRNO_BADF" if name.startswith("fd_") else "__WASI_ERRNO_NOTCAPABLE"
            body = f"return {code};"
        lines.append(f"__wasi_errno_t __wrap_{symbol}{args} {{ {body} }}")
        wrapped.append("-Wl,--wrap=" + symbol)
    return "\n".join(lines) + "\n", wrapped
