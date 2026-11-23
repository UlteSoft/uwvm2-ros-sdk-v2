/** Read-only projections of std_msgs/Time over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // data_sec
    if (!field(4, 1, 0, wanted == 1, index)) return false; // data_nsec
    return finish();
}

/** Last successfully decoded data_sec. */
export let data_sec: u32 = 0;

/** Validate the complete request or reply span, then publish data_sec. */
export function read_data_sec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    data_sec = <u32>bits;
    return true;
}

/** Last successfully decoded data_nsec. */
export let data_nsec: u32 = 0;

/** Validate the complete request or reply span, then publish data_nsec. */
export function read_data_nsec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    data_nsec = <u32>bits;
    return true;
}
