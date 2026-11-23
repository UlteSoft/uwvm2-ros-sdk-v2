/** Read-only projections of flexiv_msgs/Digital over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // pin
    if (!field(1, 1, 1, wanted == 1, index)) return false; // state
    return finish();
}

/** Last successfully decoded pin. */
export let pin: u8 = 0;

/** Validate the complete request or reply span, then publish pin. */
export function read_pin(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    pin = <u8>bits;
    return true;
}

/** Last successfully decoded state. */
export let state: bool = false;

/** Validate the complete request or reply span, then publish state. */
export function read_state(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    state = bits != 0;
    return true;
}
