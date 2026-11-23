//! Read-only projections of kortex_driver/ActuatorCyclic_Feedback.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // feedback_id_identifier
    Field(4, 1, 0), // status_flags
    Field(4, 1, 0), // jitter_comm
    Field(4, 1, 0), // position
    Field(4, 1, 0), // velocity
    Field(4, 1, 0), // torque
    Field(4, 1, 0), // current_motor
    Field(4, 1, 0), // voltage
    Field(4, 1, 0), // temperature_motor
    Field(4, 1, 0), // temperature_core
    Field(4, 1, 0), // fault_bank_a
    Field(4, 1, 0), // fault_bank_b
    Field(4, 1, 0), // warning_bank_a
    Field(4, 1, 0), // warning_bank_b
];

/// Read feedback_id_identifier.
pub fn read_feedback_id_identifier(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as u32)
}

/// Read jitter_comm.
pub fn read_jitter_comm(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(bits as u32)
}

/// Read voltage.
pub fn read_voltage(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 7, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read temperature_motor.
pub fn read_temperature_motor(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 8, 0)?;
    Some(f32::from_bits(bits as u32))
}
