import * as observation from "./uwrosv2/platform/ros2/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_sec(size) || observation.sec != -2) unreachable();
    if (observation.read_sec(size - 1)) unreachable();
    if (!observation.read_nanosec(size) || observation.nanosec != 300000000) unreachable();
    if (observation.read_nanosec(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0xfffffffe00000100);
    writeByte(8, 0);
    writeByte(9, 163);
    writeByte(10, 225);
    writeByte(11, 17);
    check(12);
    writeWord(0, 0xfeffffff00000000);
    writeByte(8, 17);
    writeByte(9, 225);
    writeByte(10, 163);
    writeByte(11, 0);
    check(12);
}
