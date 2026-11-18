package main

import (
    "runtime"
    "unsafe"
)

// Keep all backing allocations live and record their actual linear addresses.
var live [64][]byte
var examined int

func parts(b []byte) (base, size, tag uintptr) {
    p := uintptr(unsafe.Pointer(&b[0]))
    return p & 0x0fffffff, (uintptr(cap(b)) + 15) &^ 15, p >> 28
}

func allocate(i int, n int) {
    b := make([]byte, n)
    base, size, tag := parts(b)
    if tag == 0 || b[n-1] != 0 { panic("allocation") }
    for j, peer := range live {
        if j == i || peer == nil { continue }
        p, s, t := parts(peer)
        var gap uintptr
        if p < base {
            if base-p < s { panic("overlap") }
            gap = base-p-s
        } else {
            if p-base < size { panic("overlap") }
            gap = p-base-size
        }
        if gap <= 64 {
            examined++
            if tag == t { panic("neighbor tags") }
        }
    }
    b[n-1] = byte(i+1)
    live[i] = b
}

func main() {
    for i := range live { allocate(i, 13+i%7) }
    for round := 0; round < 8; round++ {
        for i := range live {
            if i%2 == round%2 {
                live[i] = nil
            }
        }
        runtime.GC()
        for i, b := range live {
            if b == nil { allocate(i, 15+(i+round)%8) } else if b[len(b)-1] != byte(i+1) { panic("lost data") }
        }
    }
    if examined < 512 { panic("insufficient close pairs") }
}
