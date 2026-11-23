import * as observation from "uwrosv2/platform/kuka/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x03,
    0x00
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x03,
    0x00
]);

function check(data: Uint8Array): void {
    if (observation.read_cycle_time(data) !== 2) throw Error("cycle_time");
    if (observation.read_cycle_time(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated cycle_time");
    if (observation.read_drives_powered(data) !== true) throw Error("drives_powered");
    if (observation.read_drives_powered(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated drives_powered");
    if (observation.read_guard_stop(data) !== false) throw Error("guard_stop");
    if (observation.read_guard_stop(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated guard_stop");
    if (observation.read_operation_mode(data) !== 3) throw Error("operation_mode");
    if (observation.read_operation_mode(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated operation_mode");
}

check(sample);
check(bigEndian);
