//! Read-only projections of Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // clock_sec
    Field(4, 1, 0), // clock_nanosec
];

/// Read clock_sec.
pub fn read_clock_sec(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as i32)
}

/// Read clock_nanosec.
pub fn read_clock_nanosec(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits as u32)
}
