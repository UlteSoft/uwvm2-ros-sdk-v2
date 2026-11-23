/** Read-only projections of booster_interface/ImuState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 3, 0, wanted == 0, index)) return false; // rpy
    if (!field(4, 3, 0, wanted == 1, index)) return false; // gyro
    if (!field(4, 3, 0, wanted == 2, index)) return false; // acc
    return finish();
}

/** Last successfully decoded rpy. */
export let rpy: f32 = 0;

/** Validate the complete request or reply span, then publish rpy. */
export function read_rpy(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 0, index, fromReply)) return false;
    rpy = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded gyro. */
export let gyro: f32 = 0;

/** Validate the complete request or reply span, then publish gyro. */
export function read_gyro(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 1, index, fromReply)) return false;
    gyro = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded acc. */
export let acc: f32 = 0;

/** Validate the complete request or reply span, then publish acc. */
export function read_acc(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 2, index, fromReply)) return false;
    acc = reinterpret<f32>(<u32>bits);
    return true;
}
