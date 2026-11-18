//go:build wasip1

package runtime

import _ "unsafe" // go:linkname

// libc constructors
//
//export __wasm_call_ctors
func __wasm_call_ctors()

func init() { __wasm_call_ctors() }

//go:linkname os_runtime_args os.runtime_args
func os_runtime_args() []string { return nil }

func ticksToNanoseconds(ticks timeUnit) int64 {
	return int64(ticks)
}

func nanosecondsToTicks(ns int64) timeUnit {
	return timeUnit(ns)
}

const timePrecisionNanoseconds = 1000 // TODO: how can we determine the appropriate `precision`?

// Blocking waits belong to the deployment-owned ROS wait service.
func sleepTicks(d timeUnit) {
	if d > 0 {
		trap()
	}
}

func ticks() timeUnit {
	var ns uint64
	if clock_time_get(1, timePrecisionNanoseconds, &ns) != 0 {
		trap()
	}
	return timeUnit(ns)
}

//go:wasmimport wasi_snapshot_preview1 clock_time_get
func clock_time_get(clockid uint32, precision uint64, time *uint64) (errno uint16)
