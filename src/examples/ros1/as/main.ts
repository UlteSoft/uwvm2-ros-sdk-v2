import * as observation from "./uwrosv2/platform/ros1/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_data_sec(size) || observation.data_sec != 301) unreachable();
    if (observation.read_data_sec(size - 1)) unreachable();
    if (!observation.read_data_nsec(size) || observation.data_nsec != 750000000) unreachable();
    if (observation.read_data_nsec(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x2cb417800000012d);
    check(8);
}
