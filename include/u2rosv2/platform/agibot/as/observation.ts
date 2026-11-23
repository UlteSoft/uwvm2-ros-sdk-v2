/** Read-only projections of aimdk_msgs/JointState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(0, 1, 0, wanted == 0, index)) return false; // name
    if (!field(8, 1, 0, wanted == 1, index)) return false; // position
    if (!field(8, 1, 0, wanted == 2, index)) return false; // velocity
    if (!field(8, 1, 0, wanted == 3, index)) return false; // effort
    if (!field(2, 1, 0, wanted == 4, index)) return false; // error_code
    return finish();
}

/** Last successfully decoded position. */
export let position: f64 = 0;

/** Validate the complete request or reply span, then publish position. */
export function read_position(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    position = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded velocity. */
export let velocity: f64 = 0;

/** Validate the complete request or reply span, then publish velocity. */
export function read_velocity(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    velocity = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded effort. */
export let effort: f64 = 0;

/** Validate the complete request or reply span, then publish effort. */
export function read_effort(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    effort = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded error_code. */
export let error_code: u16 = 0;

/** Validate the complete request or reply span, then publish error_code. */
export function read_error_code(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    error_code = <u16>bits;
    return true;
}
