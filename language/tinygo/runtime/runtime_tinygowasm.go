//go:build tinygo.wasm && !wasm_unknown && !wasip2

// This file is for wasm/wasip1 and for wasm/js, which both use much of the
// WASIp1 API.

package runtime

import _ "unsafe" // go:linkname

// See:
// https://github.com/WebAssembly/WASI/blob/main/phases/snapshot/docs.md#-proc_exitrval-exitcode
//
//go:wasmimport wasi_snapshot_preview1 proc_exit
func proc_exit(exitcode uint32)

// WROS compute modules have no console. A direct print cannot succeed.
func putchar(c byte) { trap() }

func getchar() byte { trap(); return 0 }

func buffered() int {
	// No host input is buffered.
	return 0
}

//go:linkname now time.now
func now() (sec int64, nsec int32, mono int64) {
	mono = nanotime()
	var real uint64
	if clock_time_get(0, timePrecisionNanoseconds, &real) != 0 {
		trap()
	}
	sec = int64(real / 1000000000)
	nsec = int32(real % 1000000000)
	return
}

// Abort executes the wasm 'unreachable' instruction.
func abort() {
	trap()
}

//go:linkname syscall_Exit syscall.Exit
func syscall_Exit(code int) {
	proc_exit(uint32(code))
}

func mainReturnExit() {
	syscall_Exit(0)
}

// TinyGo does not yet support any form of parallelism on WebAssembly, so these
// can be left empty.

//go:linkname procPin sync/atomic.runtime_procPin
func procPin() {
}

//go:linkname procUnpin sync/atomic.runtime_procUnpin
func procUnpin() {
}

// runtime.initRand has an upstream no-hardware fallback for map hashes.
func hardwareRand() (n uint64, ok bool) { return 0, false }

// int *__errno_location(void);
//
//export __errno_location
func libc_errno_location() *int32
