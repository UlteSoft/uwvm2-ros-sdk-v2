/** Read-only projections of turtlebot3_msgs/SensorState over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

export const BUMPER_FORWARD: i32 = 1;
export const BUMPER_BACKWARD: i32 = 2;
export const CLIFF: i32 = 1;
export const SONAR: i32 = 1;
export const ILLUMINATION: i32 = 1;
export const BUTTON0: i32 = 1;
export const BUTTON1: i32 = 2;
export const ERROR_LEFT_MOTOR: i32 = 1;
export const ERROR_RIGHT_MOTOR: i32 = 2;
export const TORQUE_ON: i32 = 1;
export const TORQUE_OFF: i32 = 2;
function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // header_seq
    if (!field(4, 1, 0, wanted == 1, index)) return false; // header_stamp_sec
    if (!field(4, 1, 0, wanted == 2, index)) return false; // header_stamp_nsec
    if (!field(0, 1, 0, wanted == 3, index)) return false; // header_frame_id
    if (!field(1, 1, 0, wanted == 4, index)) return false; // bumper
    if (!field(4, 1, 0, wanted == 5, index)) return false; // cliff
    if (!field(4, 1, 0, wanted == 6, index)) return false; // sonar
    if (!field(4, 1, 0, wanted == 7, index)) return false; // illumination
    if (!field(1, 1, 0, wanted == 8, index)) return false; // led
    if (!field(1, 1, 0, wanted == 9, index)) return false; // button
    if (!field(1, 1, 1, wanted == 10, index)) return false; // torque
    if (!field(4, 1, 0, wanted == 11, index)) return false; // left_encoder
    if (!field(4, 1, 0, wanted == 12, index)) return false; // right_encoder
    if (!field(4, 1, 0, wanted == 13, index)) return false; // battery
    return finish();
}

/** Last successfully decoded bumper. */
export let bumper: u8 = 0;

/** Validate the complete request or reply span, then publish bumper. */
export function read_bumper(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    bumper = <u8>bits;
    return true;
}

/** Last successfully decoded left_encoder. */
export let left_encoder: i32 = 0;

/** Validate the complete request or reply span, then publish left_encoder. */
export function read_left_encoder(size: u32, fromReply: bool = false): bool {
    if (!project(size, 11, 0, fromReply)) return false;
    left_encoder = <i32>bits;
    return true;
}

/** Last successfully decoded right_encoder. */
export let right_encoder: i32 = 0;

/** Validate the complete request or reply span, then publish right_encoder. */
export function read_right_encoder(size: u32, fromReply: bool = false): bool {
    if (!project(size, 12, 0, fromReply)) return false;
    right_encoder = <i32>bits;
    return true;
}

/** Last successfully decoded battery. */
export let battery: f32 = 0;

/** Validate the complete request or reply span, then publish battery. */
export function read_battery(size: u32, fromReply: bool = false): bool {
    if (!project(size, 13, 0, fromReply)) return false;
    battery = reinterpret<f32>(<u32>bits);
    return true;
}
