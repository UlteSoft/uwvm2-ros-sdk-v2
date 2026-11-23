//! Read-only projections of kuavo_msgs/BatteryInfo.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // battery_id
    Field(4, 1, 0), // voltage
    Field(4, 1, 0), // current
    Field(4, 1, 0), // remaining_capacity
    Field(4, 1, 0), // full_capacity
    Field(1, 1, 0), // percentage
    Field(2, 1, 0), // cycle_count
    Field(4, 1, 0), // protection_flags
    Field(2, 6, 0), // temperatures
    Field(4, 1, 0), // timestamp_sec
    Field(4, 1, 0), // timestamp_nsec
];

/// Read voltage.
pub fn read_voltage(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(bits as u32)
}

/// Read current.
pub fn read_current(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(bits as i32)
}

/// Read percentage.
pub fn read_percentage(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 0, LAYOUT, 5, 0)?;
    Some(bits as u8)
}

/// Read temperatures at a zero-based index.
pub fn read_temperatures(data: &[u8], index: usize) -> Option<i16> {
    let bits = reader::project(data, 0, LAYOUT, 8, index)?;
    Some(bits as i16)
}
