#include <stdio.h>
#include <stdlib.h>

_Noreturn void __assert_fail(const char *expr, const char *file, int line, const char *func)
{
// Assertions remain fatal; the VM records the trap without granting stderr.
#if !defined(__WROS_NO_HOST_DIAGNOSTICS)
	fprintf(stderr, "Assertion failed: %s (%s: %s: %d)\n", expr, file, func, line);
#endif
	abort();
}
