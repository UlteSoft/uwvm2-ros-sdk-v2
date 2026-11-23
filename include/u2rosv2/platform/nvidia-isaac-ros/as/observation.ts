/** Read-only projections of isaac_ros_tensor_list_interfaces/TensorShape over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // rank
    if (!field(4, 0, 0, wanted == 1, index)) return false; // dims
    return finish();
}

/** Last successfully decoded rank. */
export let rank: u8 = 0;

/** Validate the complete request or reply span, then publish rank. */
export function read_rank(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    rank = <u8>bits;
    return true;
}

/** Last successfully decoded dims. */
export let dims: u32 = 0;

/** Validate the complete request or reply span, then publish dims. */
export function read_dims(size: u32, index: u32, fromReply: bool = false): bool {
    if (!project(size, 1, index, fromReply)) return false;
    dims = <u32>bits;
    return true;
}
