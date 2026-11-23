/** Read-only projections of limxsdk::msg::perception_msgs::HeightEstimateResult over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // header_seq
    if (!field(4, 1, 0, wanted == 1, index)) return false; // header_stamp_sec
    if (!field(4, 1, 0, wanted == 2, index)) return false; // header_stamp_nsec
    if (!field(0, 1, 0, wanted == 3, index)) return false; // header_frame_id
    if (!field(8, 1, 0, wanted == 4, index)) return false; // estimate_height
    if (!field(0, 1, 0, wanted == 5, index)) return false; // desc
    return finish();
}

/** Last successfully decoded estimate_height. */
export let estimate_height: f64 = 0;

/** Validate the complete request or reply span, then publish estimate_height. */
export function read_estimate_height(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    estimate_height = reinterpret<f64>(bits);
    return true;
}

/** Last successfully decoded header_seq. */
export let header_seq: u32 = 0;

/** Validate the complete request or reply span, then publish header_seq. */
export function read_header_seq(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    header_seq = <u32>bits;
    return true;
}
