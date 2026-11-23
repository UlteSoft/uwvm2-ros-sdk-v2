/** Read-only projections of kuka_driver_interfaces/KssStatus over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

export const UNSPECIFIED: i32 = 0;
export const JOINT_POSITION_CONTROL: i32 = 1;
export const CARTESIAN_POSITION_CONTROL: i32 = 5;
export const RSI_4MS: i32 = 1;
export const RSI_12MS: i32 = 2;
export const T1: i32 = 1;
export const T2: i32 = 2;
export const AUT: i32 = 3;
export const EXT: i32 = 4;
function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // control_mode
    if (!field(1, 1, 0, wanted == 1, index)) return false; // cycle_time
    if (!field(1, 1, 1, wanted == 2, index)) return false; // drives_powered
    if (!field(1, 1, 1, wanted == 3, index)) return false; // emergency_stop
    if (!field(1, 1, 1, wanted == 4, index)) return false; // guard_stop
    if (!field(1, 1, 1, wanted == 5, index)) return false; // in_motion
    if (!field(1, 1, 1, wanted == 6, index)) return false; // motion_possible
    if (!field(1, 1, 0, wanted == 7, index)) return false; // operation_mode
    if (!field(1, 1, 1, wanted == 8, index)) return false; // robot_stopped
    return finish();
}

/** Last successfully decoded cycle_time. */
export let cycle_time: u8 = 0;

/** Validate the complete request or reply span, then publish cycle_time. */
export function read_cycle_time(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    cycle_time = <u8>bits;
    return true;
}

/** Last successfully decoded drives_powered. */
export let drives_powered: bool = false;

/** Validate the complete request or reply span, then publish drives_powered. */
export function read_drives_powered(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    drives_powered = bits != 0;
    return true;
}

/** Last successfully decoded guard_stop. */
export let guard_stop: bool = false;

/** Validate the complete request or reply span, then publish guard_stop. */
export function read_guard_stop(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    guard_stop = bits != 0;
    return true;
}

/** Last successfully decoded operation_mode. */
export let operation_mode: u8 = 0;

/** Validate the complete request or reply span, then publish operation_mode. */
export function read_operation_mode(size: u32, fromReply: bool = false): bool {
    if (!project(size, 7, 0, fromReply)) return false;
    operation_mode = <u8>bits;
    return true;
}
