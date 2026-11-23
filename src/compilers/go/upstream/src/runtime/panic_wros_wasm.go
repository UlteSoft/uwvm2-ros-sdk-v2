//go:build wasip1 && wasm && u2ros_eh

package runtime

//go:nosplit
func wasmUnrecoveredPanic() { wasmThrowPanic() }

func wasmThrowPanic()
