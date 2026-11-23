#include "wasi_thread_start.h"

#ifdef __wasm64__
#define PTR_TYPE i64
#define PTR_LOAD i64.load
#define PTR_CONST i64.const
#define ARGS_LOCAL 2
#else
#define PTR_TYPE i32
#define PTR_LOAD i32.load
#define PTR_CONST i32.const
#define ARGS_LOCAL 1
#endif

	.text

	.export_name	wasi_thread_start, wasi_thread_start

	.globaltype	__stack_pointer, PTR_TYPE
	.globaltype	__tls_base, PTR_TYPE
	.functype	__wasi_thread_start_C (i32, PTR_TYPE) -> ()
#ifdef __WASM_MEMTAG__
	.functype	__wasm_install_tls_v1 (PTR_TYPE) -> ()
#endif

	.hidden	wasi_thread_start
	.globl	wasi_thread_start
	.type	wasi_thread_start,@function

wasi_thread_start:
	.functype	wasi_thread_start (i32, i32) -> ()
#ifdef __wasm64__
	.local i64
	local.get   1
#ifdef __WASM_MEMTAG__
	i32.const   -WASI_THREAD_START_ALIGNMENT
	i32.and
	i64.extend_i32_u
	local.get   1
	i64.extend_i32_u
	i64.const   WASI_THREAD_START_TAG_SHIFT
	i64.shl
	i64.or
#else
	i64.extend_i32_u
#endif
	local.set   ARGS_LOCAL
#endif

	// Set up the minimum C environment.
	local.get   ARGS_LOCAL
	PTR_LOAD    0  # stack
	global.set  __stack_pointer

	local.get   ARGS_LOCAL
	PTR_LOAD    __SIZEOF_POINTER__  # tls_base
#ifdef __WASM_MEMTAG__
	call        __wasm_install_tls_v1
#else
	global.set  __tls_base
#endif

	// Make the C function do the rest of work.
	local.get   0  # tid
	local.get   ARGS_LOCAL
	call __wasi_thread_start_C

	// Unlock thread list. (as CLONE_CHILD_CLEARTID would do for Linux)
	//
	// Note: once we unlock the thread list, our "map_base" can be freed
	// by a joining thread. It's safe as we are in ASM and no longer use
	// our C stack or pthread_t. It's impossible to do this safely in C
	// because there is no way to tell the C compiler not to use C stack.
	PTR_CONST   __thread_list_lock
#ifdef __WASM_MEMTAG__
	memtag.load 0
#endif
	i32.const   0
	i32.atomic.store 0
	// As an optimization, we can check tl_lock_waiters here.
	// But for now, simply wake up unconditionally as
	// CLONE_CHILD_CLEARTID does.
	PTR_CONST   __thread_list_lock
#ifdef __WASM_MEMTAG__
	memtag.load 0
#endif
	i32.const   1
	memory.atomic.notify 0
	drop

	end_function
