import * as observation from "./uwrosv2/platform/trossen/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_temps(size, 1) || observation.temps != 41) unreachable();
    if (observation.read_temps(size - 1, 1)) unreachable();
    if (observation.read_temps(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000600000002);
    writeWord(8, 0x000630746e696f6a);
    writeWord(16, 0x31746e696f6a0000);
    writeWord(24, 0x0000000000000002);
    writeByte(32, 41);
    writeByte(33, 0);
    writeByte(34, 0);
    writeByte(35, 0);
    check(36);
}
