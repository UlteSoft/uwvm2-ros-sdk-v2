/** Read-only projections of rm_ros_interfaces/Jointerrorcode over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(2, 0, 0, wanted == 0, index)) return false; // joint_error
    if (!field(1, 1, 0, wanted == 1, index)) return false; // dof
    return finish();
}

/** Last successfully decoded joint_error. */
export let joint_error: u16 = 0;

/** Validate the complete request or reply span, then publish joint_error. */
export function read_joint_error(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 0, index, fromReply)) return false;
    joint_error = <u16>bits;
    return true;
}

/** Last successfully decoded dof. */
export let dof: u8 = 0;

/** Validate the complete request or reply span, then publish dof. */
export function read_dof(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    dof = <u8>bits;
    return true;
}
