import * as observation from "./uwrosv2/platform/boston_dynamics/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_x(size, 1) || observation.x != -0.5) unreachable();
    if (observation.read_x(size - 1, 1)) unreachable();
    if (observation.read_x(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_y(size, 1) || observation.y != 1.25) unreachable();
    if (observation.read_y(size - 1, 1)) unreachable();
    if (observation.read_y(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_z(size, 1) || observation.z != 0.75) unreachable();
    if (observation.read_z(size - 1, 1)) unreachable();
    if (observation.read_z(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000000);
    writeWord(8, 0xbf00000000000000);
    writeWord(16, 0x3f4000003fa00000);
    check(24);
}
