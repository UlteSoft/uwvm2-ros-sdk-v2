/** Read-only projections of xarm_msgs/IOState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // digital_1
    if (!field(4, 1, 0, wanted == 1, index)) return false; // digital_2
    if (!field(4, 1, 0, wanted == 2, index)) return false; // analog_1
    if (!field(4, 1, 0, wanted == 3, index)) return false; // analog_2
    return finish();
}

/** Last successfully decoded digital_1. */
export let digital_1: i32 = 0;

/** Validate the complete request or reply span, then publish digital_1. */
export function read_digital_1(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    digital_1 = <i32>bits;
    return true;
}

/** Last successfully decoded digital_2. */
export let digital_2: i32 = 0;

/** Validate the complete request or reply span, then publish digital_2. */
export function read_digital_2(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    digital_2 = <i32>bits;
    return true;
}

/** Last successfully decoded analog_1. */
export let analog_1: f32 = 0;

/** Validate the complete request or reply span, then publish analog_1. */
export function read_analog_1(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    analog_1 = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded analog_2. */
export let analog_2: f32 = 0;

/** Validate the complete request or reply span, then publish analog_2. */
export function read_analog_2(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    analog_2 = reinterpret<f32>(<u32>bits);
    return true;
}
