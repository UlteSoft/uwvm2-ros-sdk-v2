/** Read-only projections of isaac_ros_nova_interfaces/EncoderTicks. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // header_stamp_sec
    ["u32", 1, 0], // header_stamp_nanosec
    ["str", 1, 0], // header_frame_id
    ["u32", 1, 0], // left_ticks
    ["u32", 1, 0], // right_ticks
    ["u64", 1, 0], // encoder_timestamp
];

/** Read left_ticks from the complete record. Invalid data or an invalid index returns undefined. */
export function read_left_ticks(data) {
    return project(data, 1, fields, 3, 0);
}

/** Read right_ticks from the complete record. Invalid data or an invalid index returns undefined. */
export function read_right_ticks(data) {
    return project(data, 1, fields, 4, 0);
}

/** Read encoder_timestamp from the complete record. Invalid data or an invalid index returns undefined. */
export function read_encoder_timestamp(data) {
    return project(data, 1, fields, 5, 0);
}
