//! Read-only projections of limxsdk::msg::perception_msgs::HeightEstimateResult.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // header_seq
    Field(4, 1, 0), // header_stamp_sec
    Field(4, 1, 0), // header_stamp_nsec
    Field(0, 1, 0), // header_frame_id
    Field(8, 1, 0), // estimate_height
    Field(0, 1, 0), // desc
];

/// Read estimate_height.
pub fn read_estimate_height(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 0, LAYOUT, 4, 0)?;
    Some(f64::from_bits(bits))
}

/// Read header_seq.
pub fn read_header_seq(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as u32)
}
