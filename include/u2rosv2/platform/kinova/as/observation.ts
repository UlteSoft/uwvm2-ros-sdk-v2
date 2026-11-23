/** Read-only projections of kortex_driver/ActuatorCyclic_Feedback over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(4, 1, 0, wanted == 0, index)) return false; // feedback_id_identifier
    if (!field(4, 1, 0, wanted == 1, index)) return false; // status_flags
    if (!field(4, 1, 0, wanted == 2, index)) return false; // jitter_comm
    if (!field(4, 1, 0, wanted == 3, index)) return false; // position
    if (!field(4, 1, 0, wanted == 4, index)) return false; // velocity
    if (!field(4, 1, 0, wanted == 5, index)) return false; // torque
    if (!field(4, 1, 0, wanted == 6, index)) return false; // current_motor
    if (!field(4, 1, 0, wanted == 7, index)) return false; // voltage
    if (!field(4, 1, 0, wanted == 8, index)) return false; // temperature_motor
    if (!field(4, 1, 0, wanted == 9, index)) return false; // temperature_core
    if (!field(4, 1, 0, wanted == 10, index)) return false; // fault_bank_a
    if (!field(4, 1, 0, wanted == 11, index)) return false; // fault_bank_b
    if (!field(4, 1, 0, wanted == 12, index)) return false; // warning_bank_a
    if (!field(4, 1, 0, wanted == 13, index)) return false; // warning_bank_b
    return finish();
}

/** Last successfully decoded feedback_id_identifier. */
export let feedback_id_identifier: u32 = 0;

/** Validate the complete request or reply span, then publish feedback_id_identifier. */
export function read_feedback_id_identifier(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    feedback_id_identifier = <u32>bits;
    return true;
}

/** Last successfully decoded jitter_comm. */
export let jitter_comm: u32 = 0;

/** Validate the complete request or reply span, then publish jitter_comm. */
export function read_jitter_comm(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    jitter_comm = <u32>bits;
    return true;
}

/** Last successfully decoded voltage. */
export let voltage: f32 = 0;

/** Validate the complete request or reply span, then publish voltage. */
export function read_voltage(size: u32, fromReply: bool = false): bool {
    if (!project(size, 7, 0, fromReply)) return false;
    voltage = reinterpret<f32>(<u32>bits);
    return true;
}

/** Last successfully decoded temperature_motor. */
export let temperature_motor: f32 = 0;

/** Validate the complete request or reply span, then publish temperature_motor. */
export function read_temperature_motor(size: u32, fromReply: bool = false): bool {
    if (!project(size, 8, 0, fromReply)) return false;
    temperature_motor = reinterpret<f32>(<u32>bits);
    return true;
}
