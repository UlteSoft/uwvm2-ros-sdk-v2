/** Read-only projections of isaac_ros_nova_interfaces/EncoderTicks over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // header_stamp_sec
    if (!field(4, 1, 0, wanted == 1, index)) return false; // header_stamp_nanosec
    if (!field(0, 1, 0, wanted == 2, index)) return false; // header_frame_id
    if (!field(4, 1, 0, wanted == 3, index)) return false; // left_ticks
    if (!field(4, 1, 0, wanted == 4, index)) return false; // right_ticks
    if (!field(8, 1, 0, wanted == 5, index)) return false; // encoder_timestamp
    return finish();
}

/** Last successfully decoded left_ticks. */
export let left_ticks: u32 = 0;

/** Validate the complete request or reply span, then publish left_ticks. */
export function read_left_ticks(size: u32, fromReply: bool = false): bool {
    if (!project(size, 3, 0, fromReply)) return false;
    left_ticks = <u32>bits;
    return true;
}

/** Last successfully decoded right_ticks. */
export let right_ticks: u32 = 0;

/** Validate the complete request or reply span, then publish right_ticks. */
export function read_right_ticks(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    right_ticks = <u32>bits;
    return true;
}

/** Last successfully decoded encoder_timestamp. */
export let encoder_timestamp: u64 = 0;

/** Validate the complete request or reply span, then publish encoder_timestamp. */
export function read_encoder_timestamp(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    encoder_timestamp = <u64>bits;
    return true;
}
