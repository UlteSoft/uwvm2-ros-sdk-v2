import * as observation from "./uwrosv2/platform/limx/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_estimate_height(size) || observation.estimate_height != 0.625) unreachable();
    if (observation.read_estimate_height(size - 1)) unreachable();
    if (!observation.read_header_seq(size) || observation.header_seq != 524) unreachable();
    if (observation.read_header_seq(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x000000000000020c);
    writeWord(8, 0x0000000500000000);
    writeWord(16, 0x000000656d617266);
    writeWord(24, 0x0000053fe4000000);
    writeByte(32, 0);
    writeByte(33, 102);
    writeByte(34, 114);
    writeByte(35, 97);
    writeByte(36, 109);
    writeByte(37, 101);
    check(38);
}
