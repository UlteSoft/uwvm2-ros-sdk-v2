/** Read-only projections of bosdyn.api.PointCloud.data over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, -4, 0, wanted == 0, index)) return false; // xyz
    return finish();
}

/** Last successfully decoded xyz. */
export let x: f32 = 0;

/** Validate the complete request or reply span, then publish x. */
export function read_x(size: u32, index: u32, fromReply: bool = false): bool {
    if (index > 1431655765) return false;
    if (!project(size, 0, index * 3 + 0, fromReply)) return false;
    x = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded xyz. */
export let y: f32 = 0;

/** Validate the complete request or reply span, then publish y. */
export function read_y(size: u32, index: u32, fromReply: bool = false): bool {
    if (index > 1431655764) return false;
    if (!project(size, 0, index * 3 + 1, fromReply)) return false;
    y = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded xyz. */
export let z: f32 = 0;

/** Validate the complete request or reply span, then publish z. */
export function read_z(size: u32, index: u32, fromReply: bool = false): bool {
    if (index > 1431655764) return false;
    if (!project(size, 0, index * 3 + 2, fromReply)) return false;
    z = reinterpret<f32>(<u32>bits);
    return true;
}
