package address_width

#assert(ODIN_ARCH == .wasm64)
#assert(size_of(uintptr) == 8)
#assert(size_of(rawptr) == 8)
#assert(size_of(int) == 8)

Reading :: struct {
    channel: u32,
    samples: ^[4]i32,
    epoch: u64,
}
#assert(size_of(Reading) == 24)

@(export)
read :: #force_no_inline proc "c" (input: ^Reading) -> i64 {
    return i64(input.channel + u32(input.samples^[1] + input.samples^[3])) + i64(input.epoch)
}

@(export)
address_token :: #force_no_inline proc "c" (base: rawptr, stride: uintptr) -> uintptr {
    return uintptr(base) + stride
}

@(export, link_name="_start")
start :: proc "c" () {
    values := [4]i32{3, 7, 9, 11}
    reading := Reading{5, &values, 64}
    token := address_token(rawptr(uintptr(0x100000123)), 0x200000111)
    if read(&reading) != 87 || token != 0x300000234 do unreachable()
}
