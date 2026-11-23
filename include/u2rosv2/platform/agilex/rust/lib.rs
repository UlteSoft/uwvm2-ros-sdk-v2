//! Read-only projections of scout_msgs/ScoutBmsStatus.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(8, 1, 0), // soc
    Field(8, 1, 0), // soh
    Field(8, 1, 0), // battery_voltage
    Field(8, 1, 0), // battery_current
    Field(8, 1, 0), // battery_temperature
    Field(1, 1, 0), // alarm_status_1
    Field(1, 1, 0), // alarm_status_2
    Field(1, 1, 0), // warning_status_1
    Field(1, 1, 0), // warning_status_2
];

/// Read soc.
pub fn read_soc(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(f64::from_bits(bits))
}

/// Read battery_voltage.
pub fn read_battery_voltage(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(f64::from_bits(bits))
}

/// Read battery_current.
pub fn read_battery_current(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 0, LAYOUT, 3, 0)?;
    Some(f64::from_bits(bits))
}

/// Read alarm_status_1.
pub fn read_alarm_status_1(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 0, LAYOUT, 5, 0)?;
    Some(bits as u8)
}
