/** Read-only projections of myarm_communication/MyArmPumpStatus over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(1, 1, 1, wanted == 0, index)) return false; // status
    if (!field(1, 1, 0, wanted == 1, index)) return false; // pin1
    if (!field(1, 1, 0, wanted == 2, index)) return false; // pin2
    return finish();
}

/** Last successfully decoded status. */
export let status: bool = false;

/** Validate the complete request or reply span, then publish status. */
export function read_status(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    status = bits != 0;
    return true;
}

/** Last successfully decoded pin1. */
export let pin1: i8 = 0;

/** Validate the complete request or reply span, then publish pin1. */
export function read_pin1(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    pin1 = <i8>bits;
    return true;
}

/** Last successfully decoded pin2. */
export let pin2: i8 = 0;

/** Validate the complete request or reply span, then publish pin2. */
export function read_pin2(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    pin2 = <i8>bits;
    return true;
}
