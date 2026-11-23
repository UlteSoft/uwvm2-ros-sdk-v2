/** Read-only projections of pal_device_msgs/BatteryState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

export const FULL: i32 = 5;
export const HIGH: i32 = 4;
export const MEDIUM: i32 = 3;
export const LOW: i32 = 2;
export const CRITICAL_LOW: i32 = 1;
function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // charge_state
    if (!field(4, 1, 0, wanted == 1, index)) return false; // battery_percentage
    return finish();
}

/** Last successfully decoded charge_state. */
export let charge_state: i8 = 0;

/** Validate the complete request or reply span, then publish charge_state. */
export function read_charge_state(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    charge_state = <i8>bits;
    return true;
}

/** Last successfully decoded battery_percentage. */
export let battery_percentage: f32 = 0;

/** Validate the complete request or reply span, then publish battery_percentage. */
export function read_battery_percentage(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    battery_percentage = reinterpret<f32>(<u32>bits);
    return true;
}
