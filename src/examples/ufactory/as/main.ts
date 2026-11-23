import * as observation from "./uwrosv2/platform/ufactory/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_digital_1(size) || observation.digital_1 != 1) unreachable();
    if (observation.read_digital_1(size - 1)) unreachable();
    if (!observation.read_digital_2(size) || observation.digital_2 != 0) unreachable();
    if (observation.read_digital_2(size - 1)) unreachable();
    if (!observation.read_analog_1(size) || observation.analog_1 != 1.25) unreachable();
    if (observation.read_analog_1(size - 1)) unreachable();
    if (!observation.read_analog_2(size) || observation.analog_2 != 3.5) unreachable();
    if (observation.read_analog_2(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000001);
    writeWord(8, 0x406000003fa00000);
    check(16);
}
