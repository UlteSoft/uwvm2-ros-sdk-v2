//go:build !wasip1 || !wasm || !u2ros_eh

package runtime

func wasmUnrecoveredPanic() {}
