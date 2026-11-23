/** Read-only projections of Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // clock_sec
    if (!field(4, 1, 0, wanted == 1, index)) return false; // clock_nanosec
    return finish();
}

/** Last successfully decoded clock_sec. */
export let clock_sec: i32 = 0;

/** Validate the complete request or reply span, then publish clock_sec. */
export function read_clock_sec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    clock_sec = <i32>bits;
    return true;
}

/** Last successfully decoded clock_nanosec. */
export let clock_nanosec: u32 = 0;

/** Validate the complete request or reply span, then publish clock_nanosec. */
export function read_clock_nanosec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    clock_nanosec = <u32>bits;
    return true;
}
