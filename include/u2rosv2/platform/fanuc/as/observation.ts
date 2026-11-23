/** Read-only projections of fanuc_msgs/ForceSensor over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // force_x
    if (!field(4, 1, 0, wanted == 1, index)) return false; // force_y
    if (!field(4, 1, 0, wanted == 2, index)) return false; // force_z
    if (!field(4, 1, 0, wanted == 3, index)) return false; // moment_x
    if (!field(4, 1, 0, wanted == 4, index)) return false; // moment_y
    if (!field(4, 1, 0, wanted == 5, index)) return false; // moment_z
    if (!field(4, 1, 0, wanted == 6, index)) return false; // fs_type
    return finish();
}

/** Last successfully decoded force_x. */
export let force_x: f32 = 0;

/** Validate the complete request or reply span, then publish force_x. */
export function read_force_x(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    force_x = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded force_z. */
export let force_z: f32 = 0;

/** Validate the complete request or reply span, then publish force_z. */
export function read_force_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    force_z = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded moment_z. */
export let moment_z: f32 = 0;

/** Validate the complete request or reply span, then publish moment_z. */
export function read_moment_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    moment_z = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded fs_type. */
export let fs_type: u32 = 0;

/** Validate the complete request or reply span, then publish fs_type. */
export function read_fs_type(size: u32, fromReply: bool = false): bool {
    if (!project(size, 6, 0, fromReply)) return false;
    fs_type = <u32>bits;
    return true;
}
