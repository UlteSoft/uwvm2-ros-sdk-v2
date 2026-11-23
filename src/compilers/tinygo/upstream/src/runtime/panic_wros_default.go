//go:build !tinygo.wasm || !wasip1 || !u2ros_eh

package runtime

func wasmTerminalPanic() {}
