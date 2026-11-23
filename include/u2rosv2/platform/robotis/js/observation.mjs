/** Read-only projections of turtlebot3_msgs/SensorState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u32", 1, 0], // header_seq
    ["u32", 1, 0], // header_stamp_sec
    ["u32", 1, 0], // header_stamp_nsec
    ["str", 1, 0], // header_frame_id
    ["u8", 1, 0], // bumper
    ["f32", 1, 0], // cliff
    ["f32", 1, 0], // sonar
    ["f32", 1, 0], // illumination
    ["u8", 1, 0], // led
    ["u8", 1, 0], // button
    ["bool", 1, 1], // torque
    ["i32", 1, 0], // left_encoder
    ["i32", 1, 0], // right_encoder
    ["f32", 1, 0], // battery
];

export const BUMPER_FORWARD = 1;
export const BUMPER_BACKWARD = 2;
export const CLIFF = 1;
export const SONAR = 1;
export const ILLUMINATION = 1;
export const BUTTON0 = 1;
export const BUTTON1 = 2;
export const ERROR_LEFT_MOTOR = 1;
export const ERROR_RIGHT_MOTOR = 2;
export const TORQUE_ON = 1;
export const TORQUE_OFF = 2;
/** Read bumper from the complete record. Invalid data or an invalid index returns undefined. */
export function read_bumper(data) {
    return project(data, 0, fields, 4, 0);
}

/** Read left_encoder from the complete record. Invalid data or an invalid index returns undefined. */
export function read_left_encoder(data) {
    return project(data, 0, fields, 11, 0);
}

/** Read right_encoder from the complete record. Invalid data or an invalid index returns undefined. */
export function read_right_encoder(data) {
    return project(data, 0, fields, 12, 0);
}

/** Read battery from the complete record. Invalid data or an invalid index returns undefined. */
export function read_battery(data) {
    return project(data, 0, fields, 13, 0);
}
