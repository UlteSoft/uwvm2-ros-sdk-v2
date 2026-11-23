/** Read-only projections of abb_rapid_msgs/Pos over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // x
    if (!field(4, 1, 0, wanted == 1, index)) return false; // y
    if (!field(4, 1, 0, wanted == 2, index)) return false; // z
    return finish();
}

/** Last successfully decoded x. */
export let x: f32 = 0;

/** Validate the complete request or reply span, then publish x. */
export function read_x(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    x = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded y. */
export let y: f32 = 0;

/** Validate the complete request or reply span, then publish y. */
export function read_y(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    y = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded z. */
export let z: f32 = 0;

/** Validate the complete request or reply span, then publish z. */
export function read_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    z = reinterpret<f32>(<u32>bits);
    return true;
}
