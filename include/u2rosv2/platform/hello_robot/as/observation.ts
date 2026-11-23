/** Read-only projections of Wacc_Protocol_P0.unpack_status over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // ax
    if (!field(4, 1, 0, wanted == 1, index)) return false; // ay
    if (!field(4, 1, 0, wanted == 2, index)) return false; // az
    if (!field(2, 1, 0, wanted == 3, index)) return false; // a0
    if (!field(1, 1, 0, wanted == 4, index)) return false; // d0
    if (!field(1, 1, 0, wanted == 5, index)) return false; // d1
    if (!field(1, 1, 0, wanted == 6, index)) return false; // d2
    if (!field(1, 1, 0, wanted == 7, index)) return false; // d3
    if (!field(4, 1, 0, wanted == 8, index)) return false; // single_tap_count
    if (!field(4, 1, 0, wanted == 9, index)) return false; // state
    if (!field(4, 1, 0, wanted == 10, index)) return false; // timestamp
    if (!field(4, 1, 0, wanted == 11, index)) return false; // debug
    return finish();
}

/** Last successfully decoded ax. */
export let ax: f32 = 0;

/** Validate the complete request or reply span, then publish ax. */
export function read_ax(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    ax = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded az. */
export let az: f32 = 0;

/** Validate the complete request or reply span, then publish az. */
export function read_az(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    az = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded a0. */
export let a0: i16 = 0;

/** Validate the complete request or reply span, then publish a0. */
export function read_a0(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    a0 = <i16>bits;
    return true;
}

/** Last successfully decoded single_tap_count. */
export let single_tap_count: u32 = 0;

/** Validate the complete request or reply span, then publish single_tap_count. */
export function read_single_tap_count(size: u32, fromReply: bool = false): bool {
    if (!project(size, 8, 0, fromReply)) return false;
    single_tap_count = <u32>bits;
    return true;
}

/** Last successfully decoded timestamp. */
export let timestamp: u32 = 0;

/** Validate the complete request or reply span, then publish timestamp. */
export function read_timestamp(size: u32, fromReply: bool = false): bool {
    if (!project(size, 10, 0, fromReply)) return false;
    timestamp = <u32>bits;
    return true;
}
