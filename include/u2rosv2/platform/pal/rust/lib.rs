//! Read-only projections of pal_device_msgs/BatteryState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub const FULL: i32 = 5;
pub const HIGH: i32 = 4;
pub const MEDIUM: i32 = 3;
pub const LOW: i32 = 2;
pub const CRITICAL_LOW: i32 = 1;
const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // charge_state
    Field(4, 1, 0), // battery_percentage
];

/// Read charge_state.
pub fn read_charge_state(data: &[u8]) -> Option<i8> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as i8)
}

/// Read battery_percentage.
pub fn read_battery_percentage(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(f32::from_bits(bits as u32))
}
