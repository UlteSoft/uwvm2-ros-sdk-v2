/** Read-only projections of franka_msgs/Elbow over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(8, 2, 0, wanted == 0, index)) return false; // position
    if (!field(8, 2, 0, wanted == 1, index)) return false; // desired_position
    if (!field(8, 2, 0, wanted == 2, index)) return false; // commanded_position
    if (!field(8, 2, 0, wanted == 3, index)) return false; // commanded_velocity
    if (!field(8, 2, 0, wanted == 4, index)) return false; // commanded_acceleration
    return finish();
}

/** Last successfully decoded position. */
export let position: f64 = 0;

/** Validate the complete request or reply span, then publish position. */
export function read_position(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 0, index, fromReply)) return false;
    position = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded desired_position. */
export let desired_position: f64 = 0;

/** Validate the complete request or reply span, then publish desired_position. */
export function read_desired_position(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 1, index, fromReply)) return false;
    desired_position = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded commanded_position. */
export let commanded_position: f64 = 0;

/** Validate the complete request or reply span, then publish commanded_position. */
export function read_commanded_position(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 2, index, fromReply)) return false;
    commanded_position = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded commanded_velocity. */
export let commanded_velocity: f64 = 0;

/** Validate the complete request or reply span, then publish commanded_velocity. */
export function read_commanded_velocity(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 3, index, fromReply)) return false;
    commanded_velocity = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded commanded_acceleration. */
export let commanded_acceleration: f64 = 0;

/** Validate the complete request or reply span, then publish commanded_acceleration. */
export function read_commanded_acceleration(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 4, index, fromReply)) return false;
    commanded_acceleration = reinterpret<f64>(bits);
    return true;
}
