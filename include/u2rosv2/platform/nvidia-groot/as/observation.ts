/** Read-only projections of DROID observation.state over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 9, 0, wanted == 0, index)) return false; // eef_9d
    if (!field(4, 1, 0, wanted == 1, index)) return false; // gripper_position
    if (!field(4, 7, 0, wanted == 2, index)) return false; // joint_position
    return finish();
}

/** Last successfully decoded eef_9d. */
export let eef_9d: f32 = 0;

/** Validate the complete request or reply span, then publish eef_9d. */
export function read_eef_9d(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 0, index, fromReply)) return false;
    eef_9d = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded gripper_position. */
export let gripper_position: f32 = 0;

/** Validate the complete request or reply span, then publish gripper_position. */
export function read_gripper_position(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    gripper_position = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded joint_position. */
export let joint_position: f32 = 0;

/** Validate the complete request or reply span, then publish joint_position. */
export function read_joint_position(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 2, index, fromReply)) return false;
    joint_position = reinterpret<f32>(<u32>bits);
    return true;
}
