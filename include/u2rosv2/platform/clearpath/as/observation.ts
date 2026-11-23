/** Read-only projections of clearpath_dock_msgs/DockState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

export const UNDOCKED: i32 = 0;
export const DOCKED: i32 = 1;
export const IN_PROGRESS: i32 = 2;
export const FAILED: i32 = 3;
export const CANCELLED: i32 = 4;
function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // state
    return finish();
}

/** Last successfully decoded state. */
export let state: u8 = 0;

/** Validate the complete request or reply span, then publish state. */
export function read_state(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    state = <u8>bits;
    return true;
}
