#pragma once

// Supply the two Chromium debug assertions used by this component without
// pulling the browser's logging and crash-reporting services into the guest.
#define DCHECK(condition) do { if (!(condition)) __builtin_trap(); } while (0)
#define DCHECK_EQ(left, right) DCHECK((left) == (right))
