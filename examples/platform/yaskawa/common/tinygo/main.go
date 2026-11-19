// @brief Query the u2rosv2 ABI through its exact TinyGo import.
package main

//go:wasmimport uwvm_ros_v2 abi
func abi() uint32

func main() {
	if abi() != 2 { panic("ABI mismatch") }
}
