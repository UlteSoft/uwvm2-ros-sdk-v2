/** Read-only projections of scout_msgs/ScoutBmsStatus over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(8, 1, 0, wanted == 0, index)) return false; // soc
    if (!field(8, 1, 0, wanted == 1, index)) return false; // soh
    if (!field(8, 1, 0, wanted == 2, index)) return false; // battery_voltage
    if (!field(8, 1, 0, wanted == 3, index)) return false; // battery_current
    if (!field(8, 1, 0, wanted == 4, index)) return false; // battery_temperature
    if (!field(1, 1, 0, wanted == 5, index)) return false; // alarm_status_1
    if (!field(1, 1, 0, wanted == 6, index)) return false; // alarm_status_2
    if (!field(1, 1, 0, wanted == 7, index)) return false; // warning_status_1
    if (!field(1, 1, 0, wanted == 8, index)) return false; // warning_status_2
    return finish();
}

/** Last successfully decoded soc. */
export let soc: f64 = 0;

/** Validate the complete request or reply span, then publish soc. */
export function read_soc(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    soc = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded battery_voltage. */
export let battery_voltage: f64 = 0;

/** Validate the complete request or reply span, then publish battery_voltage. */
export function read_battery_voltage(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    battery_voltage = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded battery_current. */
export let battery_current: f64 = 0;

/** Validate the complete request or reply span, then publish battery_current. */
export function read_battery_current(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    battery_current = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded alarm_status_1. */
export let alarm_status_1: u8 = 0;

/** Validate the complete request or reply span, then publish alarm_status_1. */
export function read_alarm_status_1(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    alarm_status_1 = <u8>bits;
    return true;
}
