import * as observation from "./uwrosv2/platform/ros/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_x(size) || observation.x != 0.5) unreachable();
    if (observation.read_x(size - 1)) unreachable();
    if (!observation.read_y(size) || observation.y != -0.5) unreachable();
    if (observation.read_y(size - 1)) unreachable();
    if (!observation.read_z(size) || observation.z != 0.5) unreachable();
    if (observation.read_z(size - 1)) unreachable();
    if (!observation.read_w(size) || observation.w != 0.5) unreachable();
    if (observation.read_w(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000100);
    writeWord(8, 0x000000003fe00000);
    writeWord(16, 0x00000000bfe00000);
    writeWord(24, 0x000000003fe00000);
    writeByte(32, 0);
    writeByte(33, 0);
    writeByte(34, 224);
    writeByte(35, 63);
    check(36);
    writeWord(0, 0x0000e03f00000000);
    writeWord(8, 0x0000e0bf00000000);
    writeWord(16, 0x0000e03f00000000);
    writeWord(24, 0x0000e03f00000000);
    writeByte(32, 0);
    writeByte(33, 0);
    writeByte(34, 0);
    writeByte(35, 0);
    check(36);
    writeWord(0, 0x3fe0000000000000);
    writeWord(8, 0xbfe0000000000000);
    writeWord(16, 0x3fe0000000000000);
    writeWord(24, 0x3fe0000000000000);
    check(32);
}
