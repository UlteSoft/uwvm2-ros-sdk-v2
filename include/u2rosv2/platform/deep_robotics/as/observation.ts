/** Read-only projections of drdds/ImuDataValue over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // roll
    if (!field(4, 1, 0, wanted == 1, index)) return false; // pitch
    if (!field(4, 1, 0, wanted == 2, index)) return false; // yaw
    if (!field(4, 1, 0, wanted == 3, index)) return false; // omega_x
    if (!field(4, 1, 0, wanted == 4, index)) return false; // omega_y
    if (!field(4, 1, 0, wanted == 5, index)) return false; // omega_z
    if (!field(4, 1, 0, wanted == 6, index)) return false; // acc_x
    if (!field(4, 1, 0, wanted == 7, index)) return false; // acc_y
    if (!field(4, 1, 0, wanted == 8, index)) return false; // acc_z
    return finish();
}

/** Last successfully decoded roll. */
export let roll: f32 = 0;

/** Validate the complete request or reply span, then publish roll. */
export function read_roll(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    roll = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded yaw. */
export let yaw: f32 = 0;

/** Validate the complete request or reply span, then publish yaw. */
export function read_yaw(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    yaw = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded omega_z. */
export let omega_z: f32 = 0;

/** Validate the complete request or reply span, then publish omega_z. */
export function read_omega_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    omega_z = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded acc_z. */
export let acc_z: f32 = 0;

/** Validate the complete request or reply span, then publish acc_z. */
export function read_acc_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 8, 0, fromReply)) return false;
    acc_z = reinterpret<f32>(<u32>bits);
    return true;
}
