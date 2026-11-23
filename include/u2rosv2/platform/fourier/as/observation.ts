/** Read-only projections of simulator_pub_msg over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(2, size, fromReply)) return false;
    if (!field(8, 1, 0, wanted == 0, index)) return false; // timestamp
    if (!field(4, 1, 2, wanted == 1, index)) return false; // motor_num
    if (!field(8, -1, 0, wanted == 2, index)) return false; // q
    if (!field(8, -1, 0, wanted == 3, index)) return false; // q_dot
    if (!field(8, 3, 0, wanted == 4, index)) return false; // acc
    if (!field(8, 3, 0, wanted == 5, index)) return false; // omega
    if (!field(8, 4, 0, wanted == 6, index)) return false; // quat
    if (!field(8, 1, 0, wanted == 7, index)) return false; // lf_touch
    if (!field(8, 1, 0, wanted == 8, index)) return false; // rf_touch
    if (!field(8, 3, 0, wanted == 9, index)) return false; // pos
    if (!field(8, 3, 0, wanted == 10, index)) return false; // vel
    return finish();
}

/** Last successfully decoded timestamp. */
export let timestamp: i64 = 0;

/** Validate the complete request or reply span, then publish timestamp. */
export function read_timestamp(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    timestamp = <i64>bits;
    return true;
}

/** Last successfully decoded q. */
export let q: f64 = 0;

/** Validate the complete request or reply span, then publish q. */
export function read_q(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 2, index, fromReply)) return false;
    q = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded q_dot. */
export let q_dot: f64 = 0;

/** Validate the complete request or reply span, then publish q_dot. */
export function read_q_dot(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 3, index, fromReply)) return false;
    q_dot = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded lf_touch. */
export let lf_touch: f64 = 0;

/** Validate the complete request or reply span, then publish lf_touch. */
export function read_lf_touch(size: u32, fromReply: bool = false): bool {
    if (!project(size, 7, 0, fromReply)) return false;
    lf_touch = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded rf_touch. */
export let rf_touch: f64 = 0;

/** Validate the complete request or reply span, then publish rf_touch. */
export function read_rf_touch(size: u32, fromReply: bool = false): bool {
    if (!project(size, 8, 0, fromReply)) return false;
    rf_touch = reinterpret<f64>(bits);
    return true;
}
