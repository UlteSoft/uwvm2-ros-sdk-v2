import * as observation from "uwrosv2/platform/leju/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x6e, 0xbe, 0x00, 0x00, 0xcc, 0xf7, 0xff, 0xff, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xfd, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]);

function check(data: Uint8Array): void {
    if (observation.read_voltage(data) !== 48750) throw Error("voltage");
    if (observation.read_voltage(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated voltage");
    if (observation.read_current(data) !== -2100) throw Error("current");
    if (observation.read_current(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated current");
    if (observation.read_percentage(data) !== 65) throw Error("percentage");
    if (observation.read_percentage(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated percentage");
    if (observation.read_temperatures(data, 1) !== -3) throw Error("temperatures");
    if (observation.read_temperatures(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated temperatures");
    if (observation.read_temperatures(data, -1) !== undefined) throw Error("invalid index");
}

check(sample);
