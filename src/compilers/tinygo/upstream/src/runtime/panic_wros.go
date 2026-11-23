//go:build tinygo.wasm && wasip1 && u2ros_eh

package runtime

//export u2ros_tinygo_panic
func wasmTerminalPanic()
