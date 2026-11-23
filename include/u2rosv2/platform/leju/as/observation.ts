/** Read-only projections of kuavo_msgs/BatteryInfo over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // battery_id
    if (!field(4, 1, 0, wanted == 1, index)) return false; // voltage
    if (!field(4, 1, 0, wanted == 2, index)) return false; // current
    if (!field(4, 1, 0, wanted == 3, index)) return false; // remaining_capacity
    if (!field(4, 1, 0, wanted == 4, index)) return false; // full_capacity
    if (!field(1, 1, 0, wanted == 5, index)) return false; // percentage
    if (!field(2, 1, 0, wanted == 6, index)) return false; // cycle_count
    if (!field(4, 1, 0, wanted == 7, index)) return false; // protection_flags
    if (!field(2, 6, 0, wanted == 8, index)) return false; // temperatures
    if (!field(4, 1, 0, wanted == 9, index)) return false; // timestamp_sec
    if (!field(4, 1, 0, wanted == 10, index)) return false; // timestamp_nsec
    return finish();
}

/** Last successfully decoded voltage. */
export let voltage: u32 = 0;

/** Validate the complete request or reply span, then publish voltage. */
export function read_voltage(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    voltage = <u32>bits;
    return true;
}

/** Last successfully decoded current. */
export let current: i32 = 0;

/** Validate the complete request or reply span, then publish current. */
export function read_current(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    current = <i32>bits;
    return true;
}

/** Last successfully decoded percentage. */
export let percentage: u8 = 0;

/** Validate the complete request or reply span, then publish percentage. */
export function read_percentage(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    percentage = <u8>bits;
    return true;
}

/** Last successfully decoded temperatures. */
export let temperatures: i16 = 0;

/** Validate the complete request or reply span, then publish temperatures. */
export function read_temperatures(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 8, index, fromReply)) return false;
    temperatures = <i16>bits;
    return true;
}
