/** Read-only projections of kortex_driver/ActuatorCyclic_Feedback. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u32", 1, 0], // feedback_id_identifier
    ["u32", 1, 0], // status_flags
    ["u32", 1, 0], // jitter_comm
    ["f32", 1, 0], // position
    ["f32", 1, 0], // velocity
    ["f32", 1, 0], // torque
    ["f32", 1, 0], // current_motor
    ["f32", 1, 0], // voltage
    ["f32", 1, 0], // temperature_motor
    ["f32", 1, 0], // temperature_core
    ["u32", 1, 0], // fault_bank_a
    ["u32", 1, 0], // fault_bank_b
    ["u32", 1, 0], // warning_bank_a
    ["u32", 1, 0], // warning_bank_b
];

/** Read feedback_id_identifier from the complete record. Invalid data or an invalid index returns undefined. */
export function read_feedback_id_identifier(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read jitter_comm from the complete record. Invalid data or an invalid index returns undefined. */
export function read_jitter_comm(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read voltage from the complete record. Invalid data or an invalid index returns undefined. */
export function read_voltage(data) {
    return project(data, 0, fields, 7, 0);
}

/** Read temperature_motor from the complete record. Invalid data or an invalid index returns undefined. */
export function read_temperature_motor(data) {
    return project(data, 0, fields, 8, 0);
}
