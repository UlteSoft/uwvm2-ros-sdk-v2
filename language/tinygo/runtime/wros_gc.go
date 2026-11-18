package runtime

import "unsafe"

//export wros_gc_raw
func mtRaw(p uintptr) uintptr

//export wros_gc_tagged
func mtTagged(p uintptr) unsafe.Pointer

//export wros_gc_claim
func mtClaim(p, n uintptr) unsafe.Pointer

//export wros_gc_retire
func mtRetire(p, n uintptr)
