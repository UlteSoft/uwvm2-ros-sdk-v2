// @brief Verify the registered permission checks without a physical device.
package main

import "unsafe"

//go:wasmimport uwvm_ros_v2 capability.open
func openCap(memory uint32, alias, size, out uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.connect
func connect(capability uint64, memory uint32, input, size, output, capacity, written uint64) uint32

//go:wasmimport uwvm_ros_v2 capability.close
func closeCap(capability uint64) uint32

func main() {
	name := [3]byte{'a','r','m'}
	var handle uint64
	reply, written := uint64(0x4321), uint64(0x1234)
	if openCap(0,uint64(uintptr(unsafe.Pointer(&name[0]))),3,uint64(uintptr(unsafe.Pointer(&handle)))) != 0 {
		panic("capability unavailable")
	}
	if connect(handle,0,0,0,uint64(uintptr(unsafe.Pointer(&reply))),8,uint64(uintptr(unsafe.Pointer(&written)))) != 13 ||
		reply != 0x4321 || written != 0x1234 || closeCap(handle) != 0 { panic("driver permission mismatch") }
}
