import * as observation from "uwrosv2/platform/agilex/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x52, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x48, 0x40,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf8, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00
]);

function check(data: Uint8Array): void {
    if (observation.read_soc(data) !== 73.5) throw Error("soc");
    if (observation.read_soc(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated soc");
    if (observation.read_battery_voltage(data) !== 48.25) throw Error("battery_voltage");
    if (observation.read_battery_voltage(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated battery_voltage");
    if (observation.read_battery_current(data) !== -1.5) throw Error("battery_current");
    if (observation.read_battery_current(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated battery_current");
    if (observation.read_alarm_status_1(data) !== 2) throw Error("alarm_status_1");
    if (observation.read_alarm_status_1(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated alarm_status_1");
}

check(sample);
