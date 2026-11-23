/* C++ thread-local destruction for statically linked WASI programs.
 * The module remains loaded until its participating threads have stopped;
 * WASI libc does not provide dlclose or unloadable C++ DSOs. */
#include <stdlib.h>

struct tls_dtor {
    void (*destroy)(void *);
    void *object;
    struct tls_dtor *next;
};

#ifdef __wasm_atomics__
static _Thread_local struct tls_dtor *dtors;
#else
static struct tls_dtor *dtors;
#endif

int __cxa_thread_atexit_impl(void (*destroy)(void *), void *object, void *dso)
{
    (void)dso;
    struct tls_dtor *entry = malloc(sizeof *entry);
    if (!entry) return -1;
    entry->destroy = destroy;
    entry->object = object;
    entry->next = dtors;
    dtors = entry;
    return 0;
}

void __wasilibc_run_tls_dtors(void)
{
    while (dtors) {
        struct tls_dtor *entry = dtors;
        void (*destroy)(void *) = entry->destroy;
        void *object = entry->object;
        dtors = entry->next;
        free(entry);
        /* A destructor may register another TLS destructor. Keep the original
         * object pointer, including its memory tag, and drain the new head. */
        destroy(object);
    }
}
