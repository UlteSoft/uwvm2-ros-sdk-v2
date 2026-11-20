// @file controller.odin
// @brief Verify ROSv2 ABI access and a stack-backed sensor filter.
package abi_probe

foreign import ros "uwvm_ros_v2"
foreign ros {
    @(link_name="abi")
    ros_abi :: proc "c" () -> u32 ---
}

@(export)
sum_four :: #force_no_inline proc "c" (samples: ^[4]i32) -> i32 {
    return samples^[0] + samples^[1] + samples^[2] + samples^[3]
}

@(export)
filter :: #force_no_inline proc "c" (v: i32) -> i32 {
    samples := [4]i32{v, v + 1, v + 2, v + 3}
    return sum_four(&samples)
}

@(export, link_name="_start")
start :: proc "c" () {
    if ros_abi() != 2 || filter(7) != 34 do unreachable()
}
