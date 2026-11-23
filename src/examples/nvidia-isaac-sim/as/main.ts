import * as observation from "./uwrosv2/platform/nvidia-isaac-sim/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_clock_sec(size) || observation.clock_sec != 5) unreachable();
    if (observation.read_clock_sec(size - 1)) unreachable();
    if (!observation.read_clock_nanosec(size) || observation.clock_nanosec != 62500000) unreachable();
    if (observation.read_clock_nanosec(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000500000100);
    writeByte(8, 160);
    writeByte(9, 172);
    writeByte(10, 185);
    writeByte(11, 3);
    check(12);
    writeWord(0, 0x0500000000000000);
    writeByte(8, 3);
    writeByte(9, 185);
    writeByte(10, 172);
    writeByte(11, 160);
    check(12);
}
