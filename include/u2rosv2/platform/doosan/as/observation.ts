/** Read-only projections of dsr_msgs/LogAlarm over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // level
    if (!field(4, 1, 0, wanted == 1, index)) return false; // group
    if (!field(4, 1, 0, wanted == 2, index)) return false; // index
    if (!field(0, 3, 0, wanted == 3, index)) return false; // param
    return finish();
}

/** Last successfully decoded level. */
export let level: i32 = 0;

/** Validate the complete request or reply span, then publish level. */
export function read_level(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    level = <i32>bits;
    return true;
}

/** Last successfully decoded group. */
export let group: i32 = 0;

/** Validate the complete request or reply span, then publish group. */
export function read_group(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    group = <i32>bits;
    return true;
}

/** Last successfully decoded index. */
export let index: i32 = 0;

/** Validate the complete request or reply span, then publish index. */
export function read_index(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    index = <i32>bits;
    return true;
}
