/** Read-only projections of grab_demo_msgs/GraspCandidate. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // header_stamp_sec
    ["u32", 1, 0], // header_stamp_nanosec
    ["str", 1, 0], // header_frame_id
    ["i32", 1, 0], // pose_header_stamp_sec
    ["u32", 1, 0], // pose_header_stamp_nanosec
    ["str", 1, 0], // pose_header_frame_id
    ["f64", 1, 0], // pose_pose_position_x
    ["f64", 1, 0], // pose_pose_position_y
    ["f64", 1, 0], // pose_pose_position_z
    ["f64", 1, 0], // pose_pose_orientation_x
    ["f64", 1, 0], // pose_pose_orientation_y
    ["f64", 1, 0], // pose_pose_orientation_z
    ["f64", 1, 0], // pose_pose_orientation_w
    ["str", 1, 0], // group_name
    ["f32", 1, 0], // confidence
    ["str", 1, 0], // object_class
];

/** Read confidence from the complete record. Invalid data or an invalid index returns undefined. */
export function read_confidence(data) {
    return project(data, 1, fields, 14, 0);
}

/** Read pose_pose_position_z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_pose_pose_position_z(data) {
    return project(data, 1, fields, 8, 0);
}
