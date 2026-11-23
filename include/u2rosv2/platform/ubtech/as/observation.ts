/** Read-only projections of grab_demo_msgs/GraspCandidate over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // header_stamp_sec
    if (!field(4, 1, 0, wanted == 1, index)) return false; // header_stamp_nanosec
    if (!field(0, 1, 0, wanted == 2, index)) return false; // header_frame_id
    if (!field(4, 1, 0, wanted == 3, index)) return false; // pose_header_stamp_sec
    if (!field(4, 1, 0, wanted == 4, index)) return false; // pose_header_stamp_nanosec
    if (!field(0, 1, 0, wanted == 5, index)) return false; // pose_header_frame_id
    if (!field(8, 1, 0, wanted == 6, index)) return false; // pose_pose_position_x
    if (!field(8, 1, 0, wanted == 7, index)) return false; // pose_pose_position_y
    if (!field(8, 1, 0, wanted == 8, index)) return false; // pose_pose_position_z
    if (!field(8, 1, 0, wanted == 9, index)) return false; // pose_pose_orientation_x
    if (!field(8, 1, 0, wanted == 10, index)) return false; // pose_pose_orientation_y
    if (!field(8, 1, 0, wanted == 11, index)) return false; // pose_pose_orientation_z
    if (!field(8, 1, 0, wanted == 12, index)) return false; // pose_pose_orientation_w
    if (!field(0, 1, 0, wanted == 13, index)) return false; // group_name
    if (!field(4, 1, 0, wanted == 14, index)) return false; // confidence
    if (!field(0, 1, 0, wanted == 15, index)) return false; // object_class
    return finish();
}

/** Last successfully decoded confidence. */
export let confidence: f32 = 0;

/** Validate the complete request or reply span, then publish confidence. */
export function read_confidence(size: u32, fromReply: bool = false): bool {
    if (!project(size, 14, 0, fromReply)) return false;
    confidence = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded pose_pose_position_z. */
export let pose_pose_position_z: f64 = 0;

/** Validate the complete request or reply span, then publish pose_pose_position_z. */
export function read_pose_pose_position_z(size: u32, fromReply: bool = false): bool {
    if (!project(size, 8, 0, fromReply)) return false;
    pose_pose_position_z = reinterpret<f64>(bits);
    return true;
}
