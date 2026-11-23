import * as observation from "./uwrosv2/platform/doosan/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_level(size) || observation.level != 2) unreachable();
    if (observation.read_level(size - 1)) unreachable();
    if (!observation.read_group(size) || observation.group != 3) unreachable();
    if (observation.read_group(size - 1)) unreachable();
    if (!observation.read_index(size) || observation.index != -7) unreachable();
    if (observation.read_index(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000300000002);
    writeWord(8, 0x00000006fffffff9);
    writeWord(16, 0x000630746e696f6a);
    writeWord(24, 0x31746e696f6a0000);
    writeWord(32, 0x6e696f6a00000006);
    writeByte(40, 116);
    writeByte(41, 50);
    check(42);
}
