import * as observation from "./uwrosv2/platform/booster/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_rpy(size, 1) || observation.rpy != 0.25) unreachable();
    if (observation.read_rpy(size - 1, 1)) unreachable();
    if (observation.read_rpy(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_gyro(size, 1) || observation.gyro != -1.5) unreachable();
    if (observation.read_gyro(size - 1, 1)) unreachable();
    if (observation.read_gyro(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_acc(size, 1) || observation.acc != 9.75) unreachable();
    if (observation.read_acc(size - 1, 1)) unreachable();
    if (observation.read_acc(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000100);
    writeWord(8, 0x000000003e800000);
    writeWord(16, 0xbfc0000000000000);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0x00000000411c0000);
    check(40);
    writeWord(0, 0x0000000000000000);
    writeWord(8, 0x000000000000803e);
    writeWord(16, 0x0000c0bf00000000);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0x0000000000001c41);
    check(40);
}
