import * as observation from "./uwrosv2/platform/ubtech/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_confidence(size) || observation.confidence != 0.75) unreachable();
    if (observation.read_confidence(size - 1)) unreachable();
    if (!observation.read_pose_pose_position_z(size) || observation.pose_pose_position_z != 0.125) unreachable();
    if (observation.read_pose_pose_position_z(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000100);
    writeWord(8, 0x0000000600000000);
    writeWord(16, 0x000000656d617266);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0x6d61726600000006);
    writeWord(40, 0x0000000000000065);
    writeWord(48, 0x0000000000000000);
    writeWord(56, 0x0000000000000000);
    writeWord(64, 0x000000003fc00000);
    writeWord(72, 0x0000000000000000);
    writeWord(80, 0x0000000000000000);
    writeWord(88, 0x0000000000000000);
    writeWord(96, 0x0000000600000000);
    writeWord(104, 0x000000656d617266);
    writeWord(112, 0x000000063f400000);
    writeByte(120, 102);
    writeByte(121, 114);
    writeByte(122, 97);
    writeByte(123, 109);
    writeByte(124, 101);
    writeByte(125, 0);
    check(126);
    writeWord(0, 0x0000000000000000);
    writeWord(8, 0x0600000000000000);
    writeWord(16, 0x000000656d617266);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0x6d61726606000000);
    writeWord(40, 0x0000000000000065);
    writeWord(48, 0x0000000000000000);
    writeWord(56, 0x0000c03f00000000);
    writeWord(64, 0x0000000000000000);
    writeWord(72, 0x0000000000000000);
    writeWord(80, 0x0000000000000000);
    writeWord(88, 0x0000000000000000);
    writeWord(96, 0x0600000000000000);
    writeWord(104, 0x000000656d617266);
    writeWord(112, 0x060000000000403f);
    writeByte(120, 102);
    writeByte(121, 114);
    writeByte(122, 97);
    writeByte(123, 109);
    writeByte(124, 101);
    writeByte(125, 0);
    check(126);
}
