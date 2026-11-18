package main

import (
	"runtime"
	"runtime/volatile"
	"unsafe"
	scene "wros.local/scene"
)

type node struct {
	next *node
	data []byte
}

//go:section .wros.no_memtag
var rawData [8]byte
var taggedData [8]byte

//go:section .wros.no_memtag
func rawStack(index int) uintptr {
	var bytes [8]byte
	volatile.StoreUint8(&bytes[index&7], byte(index))
	return uintptr(volatile.LoadUint8(&bytes[index&7]))
}

var saved *node
var seen [4096]uint32
var reuses int

//go:noinline
func nodeFor(i uint32, next *node) *node {
	b := make([]byte, 73+i%17)
	if b[17] != 0 || b[len(b)-1] != 0 {
		panic("heap not cleared")
	}
	offset := (uintptr(unsafe.Pointer(&b[0])) & 0x0fffffff) / 16
	if offset >= uintptr(len(seen))*32 {
		panic("unexpected footprint")
	}
	bit := uint32(1) << (offset % 32)
	if seen[offset/32]&bit != 0 {
		reuses++
	}
	seen[offset/32] |= bit
	b[17] = byte(i + 1)
	return &node{next, b}
}

//go:noinline
func test(n uint32) {
	for i := uint32(0); i < n; i++ {
		saved = nodeFor(i, saved)
	}
	runtime.GC()
	cursor := saved
	for i := n; i > 0; i-- {
		if cursor == nil || (uintptr(unsafe.Pointer(cursor))>>28 != 0) != tagged || (uintptr(unsafe.Pointer(&cursor.data[0]))>>28 != 0) != tagged || cursor.data[17] != byte(i) {
			panic("gc lost tagged object")
		}
		cursor = cursor.next
	}
	saved = nil
}
func main() {
	a := scene.Abi()
	volatile.StoreUint8(&rawData[a&7], byte(a))
	volatile.StoreUint8(&taggedData[a&7], byte(a))
	if rawStack(int(a)) != uintptr(a) ||
		uintptr(unsafe.Pointer(&rawData[a&7]))>>28 != 0 ||
		(uintptr(unsafe.Pointer(&taggedData[a&7]))>>28 != 0) != tagged {
		panic("source instrumentation selection")
	}
	if a != 2 {
		panic("ABI")
	}
	for i := 0; i < 8; i++ {
		test(100 * a)
		runtime.GC()
	}
	var stats runtime.MemStats
	runtime.ReadMemStats(&stats)
	if stats.Mallocs < 3000 || stats.Frees < 2000 || reuses == 0 {
		panic("insufficient heap collection")
	}
}
