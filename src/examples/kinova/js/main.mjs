import * as observation from "uwrosv2/platform/kinova/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0xd2, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x42, 0x00, 0x00, 0x29, 0x42,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]);

function check(data) {
    if (observation.read_feedback_id_identifier(data) !== 1234) throw Error("feedback_id_identifier");
    if (observation.read_feedback_id_identifier(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated feedback_id_identifier");
    if (observation.read_jitter_comm(data) !== 150) throw Error("jitter_comm");
    if (observation.read_jitter_comm(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated jitter_comm");
    if (observation.read_voltage(data) !== 47.5) throw Error("voltage");
    if (observation.read_voltage(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated voltage");
    if (observation.read_temperature_motor(data) !== 42.25) throw Error("temperature_motor");
    if (observation.read_temperature_motor(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated temperature_motor");
}

check(sample);
