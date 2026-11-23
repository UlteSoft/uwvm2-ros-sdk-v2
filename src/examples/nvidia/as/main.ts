import * as observation from "./uwrosv2/platform/nvidia/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_left_ticks(size) || observation.left_ticks != 305419896) unreachable();
    if (observation.read_left_ticks(size - 1)) unreachable();
    if (!observation.read_right_ticks(size) || observation.right_ticks != 7654321) unreachable();
    if (observation.read_right_ticks(size - 1)) unreachable();
    if (!observation.read_encoder_timestamp(size) || observation.encoder_timestamp != 4294967301) unreachable();
    if (observation.read_encoder_timestamp(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000100);
    writeWord(8, 0x0000000600000000);
    writeWord(16, 0x000000656d617266);
    writeWord(24, 0x0074cbb112345678);
    writeWord(32, 0x0000000500000000);
    writeByte(40, 1);
    writeByte(41, 0);
    writeByte(42, 0);
    writeByte(43, 0);
    check(44);
    writeWord(0, 0x0000000000000000);
    writeWord(8, 0x0600000000000000);
    writeWord(16, 0x000000656d617266);
    writeWord(24, 0xb1cb740078563412);
    writeWord(32, 0x0100000000000000);
    writeByte(40, 0);
    writeByte(41, 0);
    writeByte(42, 0);
    writeByte(43, 5);
    check(44);
}
