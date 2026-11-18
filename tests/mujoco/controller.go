package main

import (
	"encoding/binary"
	"math"
	"runtime/volatile"
	"unsafe"

	scene "wros.local/scene"
)

type operation uint8

const (
	connect operation = iota
	submit
	result
	describe
	disconnect
)

func invoke(op operation, token uint64, input []byte, reply *[64]uint64) (uint32, uint64) {
	var address uint64
	if len(input) > 0 {
		address = uint64(uintptr(unsafe.Pointer(&input[0])))
	}
	var written uint64
	size := uint64(len(input))
	dst := uint64(uintptr(unsafe.Pointer(reply)))
	capacity := uint64(unsafe.Sizeof(*reply))
	count := uint64(uintptr(unsafe.Pointer(&written)))
	var code uint32
	switch op {
	case connect:
		code = scene.DriverConnect(token, 0, address, size, dst, capacity, count)
	case submit:
		code = scene.DriverSubmit(token, 0, address, size, dst, capacity, count)
	case result:
		code = scene.DriverResult(token, 0, address, size, dst, capacity, count)
	case describe:
		code = scene.DriverDescribe(token, 0, address, size, dst, capacity, count)
	case disconnect:
		code = scene.DriverDisconnect(token, 0, address, size, dst, capacity, count)
	default:
		panic("unknown driver operation")
	}
	return code, volatile.LoadUint64(&written)
}

func poll(op operation, token uint64, data []byte, reply *[64]uint64) (uint32, uint64) {
	for i := 0; i < 10000000; i++ {
		code, size := invoke(op, token, data, reply)
		if code != 11 {
			return code, size
		}
	}
	panic("receiver timeout")
}

func main() {
	alias := [5]byte{'j', 'o', 'i', 'n', 't'}
	var token uint64
	if scene.CapabilityOpen(0, uint64(uintptr(unsafe.Pointer(&alias))), 5, uint64(uintptr(unsafe.Pointer(&token)))) != 0 {
		panic("open")
	}
	token = volatile.LoadUint64(&token)
	var reply [64]uint64
	if status, _ := poll(connect, token, nil, &reply); status != 0 {
		panic("connect")
	}
	request := template
	for seq := uint64(1); seq <= steps; seq++ {
		var word [8]byte
		binary.LittleEndian.PutUint64(word[:], seq)
		copy(request[:8], word[:])
		copy(request[32:40], word[:])
		if success {
			value := 0.5
			if seq%2 == 0 {
				value = -0.5
			}
			binary.LittleEndian.PutUint64(request[targetOffset:], math.Float64bits(value))
		}
		if status, _ := poll(submit, token, request[:], &reply); status != 0 {
			panic("submit")
		}
		status, size := poll(result, token, word[:], &reply)
		if crash {
			if status != 5 && status != 13 {
				panic("unknown effect")
			}
			status, size = invoke(describe, token, nil, &reply)
			if status != 0 || size < 32 || reply[0] != 6 || reply[3] != 1 {
				panic("recovery state")
			}
		} else {
			expected := uint64(13)
			if success {
				expected = 0
			}
			if status != 0 || size < 24 || reply[0] != expected || reply[2] != seq {
				panic("result")
			}
		}
	}
	if status, _ := invoke(disconnect, token, nil, &reply); status != 0 {
		panic("disconnect")
	}
}
