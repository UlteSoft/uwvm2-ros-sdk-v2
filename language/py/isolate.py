"""@file isolate.py
@brief Compile guest-local libc permission denials using the selected sysroot's declarations.
"""
import re


def declarations(header):
    """@brief Return typed link wrappers that publish only clocks outside the interpreter.

    @details The guest receives empty argv and environment vectors. Unknown ABI
    inputs fail signature review, and wrpy checks the final import inventory.
    """
    text = re.sub(r"/\*.*?\*/", "", header.read_text(), flags=re.S)
    pattern = r"\b__wasi_errno_t\s+(__wasi_[a-z0-9_]+)\s*(\([^()]*\))\s*__attribute__\(\(__warn_unused_result__\)\);"
    prototypes = dict(re.findall(pattern, text))
    if not {"__wasi_fd_read", "__wasi_fd_write", "__wasi_path_open", "__wasi_sock_recv",
            "__wasi_random_get", "__wasi_clock_time_get"} <= prototypes.keys():
        raise ValueError("unsupported WASIp1 sysroot declaration format")
    result = ["#include <wasi/api.h>"]
    wrapped = []
    for name, args in sorted(prototypes.items()):
        if name in ("__wasi_clock_time_get", "__wasi_clock_res_get"):
            continue
        wrapped.append(name)
        error = "__WASI_ERRNO_BADF" if name.startswith("__wasi_fd_") else "__WASI_ERRNO_NOTCAPABLE"
        body = "return " + error + ";"
        if name in ("__wasi_environ_sizes_get", "__wasi_args_sizes_get"):
            body = "*retptr0 = 0; *retptr1 = 0; return __WASI_ERRNO_SUCCESS;"
        elif name in ("__wasi_environ_get", "__wasi_args_get"):
            body = "return __WASI_ERRNO_SUCCESS;"
        result.append(f"__wasi_errno_t __wrap_{name}{args} {{ {body} }}")
    result.append("void __wrap___wasi_proc_exit(__wasi_exitcode_t code) { __builtin_trap(); }")
    wrapped.append("__wasi_proc_exit")
    return "\n".join(result) + "\n", ["-Wl,--wrap=" + name for name in wrapped]
