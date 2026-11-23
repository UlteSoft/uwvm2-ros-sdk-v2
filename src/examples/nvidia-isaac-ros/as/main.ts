import * as observation from "./uwrosv2/platform/nvidia-isaac-ros/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_rank(size) || observation.rank != 2) unreachable();
    if (observation.read_rank(size - 1)) unreachable();
    if (!observation.read_dims(size, 1) || observation.dims != 640) unreachable();
    if (observation.read_dims(size - 1, 1)) unreachable();
    if (observation.read_dims(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000200000100);
    writeWord(8, 0x0000000000000002);
    writeByte(16, 128);
    writeByte(17, 2);
    writeByte(18, 0);
    writeByte(19, 0);
    check(20);
    writeWord(0, 0x0000000200000000);
    writeWord(8, 0x0000000002000000);
    writeByte(16, 0);
    writeByte(17, 0);
    writeByte(18, 2);
    writeByte(19, 128);
    check(20);
}
