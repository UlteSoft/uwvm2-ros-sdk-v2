#pragma once

#include <exception>
#include <mutex>
#include <stdexcept>

#if !defined(__wasm__) || defined(__wasm_atomics__) || defined(_REENTRANT) || !defined(__cpp_exceptions)
#error "Jazzy tf2 single-executor port requires non-atomic single-threaded Wasm with C++ exceptions"
#endif

namespace wros_tf2 {

//! A private, single-executor BufferCore cannot wait for a concurrent owner.
//! Reject same-executor re-entry. std::unique_lock releases ownership on unwind.
//! Shared-memory builds retain the original std::mutex and never include this file.
class single_executor_mutex {
    bool held_ = false;
public:
    single_executor_mutex() = default;
    single_executor_mutex(const single_executor_mutex&) = delete;
    single_executor_mutex& operator=(const single_executor_mutex&) = delete;
    void lock() {
        if (held_) throw std::logic_error("reentrant tf2 single-executor lock");
        held_ = true;
    }
    void unlock() noexcept {
        if (!held_) std::terminate();
        held_ = false;
    }
};

}
