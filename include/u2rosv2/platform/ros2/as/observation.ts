/** Read-only projections of builtin_interfaces/Duration over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // sec
    if (!field(4, 1, 0, wanted == 1, index)) return false; // nanosec
    return finish();
}

/** Last successfully decoded sec. */
export let sec: i32 = 0;

/** Validate the complete request or reply span, then publish sec. */
export function read_sec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    sec = <i32>bits;
    return true;
}

/** Last successfully decoded nanosec. */
export let nanosec: u32 = 0;

/** Validate the complete request or reply span, then publish nanosec. */
export function read_nanosec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    nanosec = <u32>bits;
    return true;
}
