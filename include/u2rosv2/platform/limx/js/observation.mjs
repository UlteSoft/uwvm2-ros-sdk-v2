/** Read-only projections of limxsdk::msg::perception_msgs::HeightEstimateResult. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u32", 1, 0], // header_seq
    ["u32", 1, 0], // header_stamp_sec
    ["u32", 1, 0], // header_stamp_nsec
    ["str", 1, 0], // header_frame_id
    ["f64", 1, 0], // estimate_height
    ["str", 1, 0], // desc
];

/** Read estimate_height from the complete record. Invalid data or an invalid index returns undefined. */
export function read_estimate_height(data) {
    return project(data, 0, fields, 4, 0);
}

/** Read header_seq from the complete record. Invalid data or an invalid index returns undefined. */
export function read_header_seq(data) {
    return project(data, 0, fields, 0, 0);
}
