/** Read-only projections of geometry_msgs/Quaternion over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(3, size, fromReply)) return false;
    if (!field(8, 1, 0, wanted == 0, index)) return false; // x
    if (!field(8, 1, 0, wanted == 1, index)) return false; // y
    if (!field(8, 1, 0, wanted == 2, index)) return false; // z
    if (!field(8, 1, 0, wanted == 3, index)) return false; // w
    return finish();
}

/** Last successfully decoded x. */
export let x: f64 = 0;

/** Validate the complete request or reply span, then publish x. */
export function read_x(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    x = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded y. */
export let y: f64 = 0;

/** Validate the complete request or reply span, then publish y. */
export function read_y(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    y = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded z. */
export let z: f64 = 0;

/** Validate the complete request or reply span, then publish z. */
export function read_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    z = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded w. */
export let w: f64 = 0;

/** Validate the complete request or reply span, then publish w. */
export function read_w(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    w = reinterpret<f64>(bits);
    return true;
}
