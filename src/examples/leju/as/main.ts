import * as observation from "./uwrosv2/platform/leju/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_voltage(size) || observation.voltage != 48750) unreachable();
    if (observation.read_voltage(size - 1)) unreachable();
    if (!observation.read_current(size) || observation.current != -2100) unreachable();
    if (observation.read_current(size - 1)) unreachable();
    if (!observation.read_percentage(size) || observation.percentage != 65) unreachable();
    if (observation.read_percentage(size - 1)) unreachable();
    if (!observation.read_temperatures(size, 1) || observation.temperatures != -3) unreachable();
    if (observation.read_temperatures(size - 1, 1)) unreachable();
    if (observation.read_temperatures(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0xfff7cc0000be6e00);
    writeWord(8, 0x00000000000000ff);
    writeWord(16, 0x0000000000004100);
    writeWord(24, 0x00000000fffd0000);
    writeWord(32, 0x0000000000000000);
    writeByte(40, 0);
    writeByte(41, 0);
    writeByte(42, 0);
    writeByte(43, 0);
    check(44);
}
