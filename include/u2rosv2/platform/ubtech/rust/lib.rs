//! Read-only projections of grab_demo_msgs/GraspCandidate.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // header_stamp_sec
    Field(4, 1, 0), // header_stamp_nanosec
    Field(0, 1, 0), // header_frame_id
    Field(4, 1, 0), // pose_header_stamp_sec
    Field(4, 1, 0), // pose_header_stamp_nanosec
    Field(0, 1, 0), // pose_header_frame_id
    Field(8, 1, 0), // pose_pose_position_x
    Field(8, 1, 0), // pose_pose_position_y
    Field(8, 1, 0), // pose_pose_position_z
    Field(8, 1, 0), // pose_pose_orientation_x
    Field(8, 1, 0), // pose_pose_orientation_y
    Field(8, 1, 0), // pose_pose_orientation_z
    Field(8, 1, 0), // pose_pose_orientation_w
    Field(0, 1, 0), // group_name
    Field(4, 1, 0), // confidence
    Field(0, 1, 0), // object_class
];

/// Read confidence.
pub fn read_confidence(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 14, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read pose_pose_position_z.
pub fn read_pose_pose_position_z(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 8, 0)?;
    Some(f64::from_bits(bits))
}
