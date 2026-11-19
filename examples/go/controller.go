// Package robot defines a register-only controller for the ROSv2 host ABI.
package robot

// Gain combines three sensor values with Go's signed 32-bit wraparound.
// @param value Scaled sensor input.
// @param scale Fixed-point scale factor.
// @param bias Fixed offset.
// @return The scaled result.
func Gain(value, scale, bias int32) int32 { return value*scale + bias }

// Start checks the explicitly selected ROSv2 ABI.
// @param abi Host ABI number passed by the Wasm entry point.
// @return Zero for ABI 2. A nonzero result traps the guest.
func Start(abi uint32) uint32 { return abi - 2 }
