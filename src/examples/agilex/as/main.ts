import * as observation from "./uwrosv2/platform/agilex/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_soc(size) || observation.soc != 73.5) unreachable();
    if (observation.read_soc(size - 1)) unreachable();
    if (!observation.read_battery_voltage(size) || observation.battery_voltage != 48.25) unreachable();
    if (observation.read_battery_voltage(size - 1)) unreachable();
    if (!observation.read_battery_current(size) || observation.battery_current != -1.5) unreachable();
    if (observation.read_battery_current(size - 1)) unreachable();
    if (!observation.read_alarm_status_1(size) || observation.alarm_status_1 != 2) unreachable();
    if (observation.read_alarm_status_1(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x4052600000000000);
    writeWord(8, 0x0000000000000000);
    writeWord(16, 0x4048200000000000);
    writeWord(24, 0xbff8000000000000);
    writeWord(32, 0x0000000000000000);
    writeByte(40, 2);
    writeByte(41, 0);
    writeByte(42, 0);
    writeByte(43, 0);
    check(44);
}
