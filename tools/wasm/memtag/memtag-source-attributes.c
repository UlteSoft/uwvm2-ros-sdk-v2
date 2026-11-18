// Compile as both C and C++ with and without translation-unit instrumentation.
// The external call forces the buffer to escape the stack-safety proof.
#ifdef __cplusplus
extern "C" {
#endif
void observe(void *);

// ON-LABEL: ordinary:
// ON: memtag.{{(random|hint)}}
// ON: call observe
// ON: memtag.store 0
// ON-LABEL: locally_uninstrumented:
// ON-NOT: memtag.
// ON: call observe
// ON-NOT: memtag.
// ON: end_function
// OFF-LABEL: ordinary:
// OFF-NOT: memtag.
// OFF: call observe
// OFF-NOT: memtag.
// OFF: end_function
// OFF-LABEL: locally_uninstrumented:
// OFF-NOT: memtag.
// OFF: call observe
// OFF-NOT: memtag.
// OFF: end_function
__attribute__((noinline)) void ordinary(void) {
    char buffer[32];
    observe(buffer);
}

__attribute__((noinline, no_sanitize("memtag"))) void locally_uninstrumented(void) {
    char buffer[32];
    observe(buffer);
}
#ifdef __cplusplus
}
#endif
