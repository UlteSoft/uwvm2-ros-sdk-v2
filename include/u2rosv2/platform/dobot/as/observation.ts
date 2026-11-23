/** Read-only projections of dobot_msgs_v4/RobotStatus over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(1, 1, 1, wanted == 0, index)) return false; // is_enable
    if (!field(1, 1, 1, wanted == 1, index)) return false; // is_connected
    return finish();
}

/** Last successfully decoded is_enable. */
export let is_enable: bool = false;

/** Validate the complete request or reply span, then publish is_enable. */
export function read_is_enable(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    is_enable = bits != 0;
    return true;
}

/** Last successfully decoded is_connected. */
export let is_connected: bool = false;

/** Validate the complete request or reply span, then publish is_connected. */
export function read_is_connected(size: u32, fromReply: bool = false): bool {
    if (!project(size, 1, 0, fromReply)) return false;
    is_connected = bits != 0;
    return true;
}
