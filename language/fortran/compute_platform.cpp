/** @file
 * @brief Guest-only Flang compute runtime environment.
 * @details Intrinsic allocation uses the default Fortran alignment and supports
 * empty arrays. The process environment, native descriptor I/O and host process
 * termination are outside this library. A violated internal invariant traps the
 * current guest. Recoverable allocation statuses use Flang's STAT/ERRMSG path.
 */
#include "flang-rt/runtime/environment.h"
#include "flang-rt/runtime/terminator.h"

namespace Fortran::runtime {
ExecutionEnvironment executionEnvironment{};

[[noreturn]] void Terminator::CheckFailed(const char *, const char *, int) const {
  __builtin_trap();
}

[[noreturn]] void Terminator::CheckFailed(const char *) const {
  __builtin_trap();
}
} // namespace Fortran::runtime
