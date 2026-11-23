/** Read-only projections of interbotix_xs_msgs/JointTemps over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(0, 0, 0, wanted == 0, index)) return false; // names
    if (!field(4, 0, 0, wanted == 1, index)) return false; // temps
    return finish();
}

/** Last successfully decoded temps. */
export let temps: i32 = 0;

/** Validate the complete request or reply span, then publish temps. */
export function read_temps(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 1, index, fromReply)) return false;
    temps = <i32>bits;
    return true;
}
