import * as observation from "./uwrosv2/platform/abb/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_x(size) || observation.x != 12.5) unreachable();
    if (observation.read_x(size - 1)) unreachable();
    if (!observation.read_y(size) || observation.y != -2.75) unreachable();
    if (observation.read_y(size - 1)) unreachable();
    if (!observation.read_z(size) || observation.z != 0.5) unreachable();
    if (observation.read_z(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0xc030000041480000);
    writeByte(8, 0);
    writeByte(9, 0);
    writeByte(10, 0);
    writeByte(11, 63);
    check(12);
}
