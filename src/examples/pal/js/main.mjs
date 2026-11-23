import * as observation from "uwrosv2/platform/pal/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x03, 0x00, 0x00, 0x87, 0x42
]);

function check(data) {
    if (observation.read_charge_state(data) !== 3) throw Error("charge_state");
    if (observation.read_charge_state(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated charge_state");
    if (observation.read_battery_percentage(data) !== 67.5) throw Error("battery_percentage");
    if (observation.read_battery_percentage(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated battery_percentage");
}

check(sample);
