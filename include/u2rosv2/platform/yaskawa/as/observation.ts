/** Read-only projections of motoros2_interfaces/ErrorInfo over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // number
    if (!field(0, 1, 0, wanted == 1, index)) return false; // message
    if (!field(4, 1, 0, wanted == 2, index)) return false; // sub_code
    if (!field(4, 1, 0, wanted == 3, index)) return false; // datetime_sec
    if (!field(4, 1, 0, wanted == 4, index)) return false; // datetime_nanosec
    return finish();
}

/** Last successfully decoded number. */
export let number: u32 = 0;

/** Validate the complete request or reply span, then publish number. */
export function read_number(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    number = <u32>bits;
    return true;
}

/** Last successfully decoded sub_code. */
export let sub_code: i32 = 0;

/** Validate the complete request or reply span, then publish sub_code. */
export function read_sub_code(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    sub_code = <i32>bits;
    return true;
}

/** Last successfully decoded datetime_sec. */
export let datetime_sec: i32 = 0;

/** Validate the complete request or reply span, then publish datetime_sec. */
export function read_datetime_sec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    datetime_sec = <i32>bits;
    return true;
}

/** Last successfully decoded datetime_nanosec. */
export let datetime_nanosec: u32 = 0;

/** Validate the complete request or reply span, then publish datetime_nanosec. */
export function read_datetime_nanosec(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    datetime_nanosec = <u32>bits;
    return true;
}
