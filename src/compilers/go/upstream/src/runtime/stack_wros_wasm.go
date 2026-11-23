//go:build wasip1 && wasm && u2ros_mte

package runtime

// The pool owns the raw span before claim and after release. Goroutine stack
// bounds, SP, interior pointers and stack-copy deltas use the claimed address.
//
//go:nosplit
func wasmStackBounds(base, size uintptr) stack {
	tagged := wasmStackClaim(base, size)
	return stack{tagged, tagged + size}
}

//go:nosplit
func wasmStackReturn(base, size uintptr) uintptr {
	return wasmStackRelease(base, size)
}

func wasmStackClaim(base, size uintptr) uintptr
func wasmStackRelease(base, size uintptr) uintptr
