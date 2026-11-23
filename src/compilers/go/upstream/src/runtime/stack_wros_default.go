//go:build !wasip1 || !wasm || !u2ros_mte

package runtime

func wasmStackBounds(base, size uintptr) stack   { return stack{base, base + size} }
func wasmStackReturn(base, size uintptr) uintptr { return base }
