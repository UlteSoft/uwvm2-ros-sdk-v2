import * as observation from "./uwrosv2/platform/agibot/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_position(size) || observation.position != 0.5) unreachable();
    if (observation.read_position(size - 1)) unreachable();
    if (!observation.read_velocity(size) || observation.velocity != -0.25) unreachable();
    if (observation.read_velocity(size - 1)) unreachable();
    if (!observation.read_effort(size) || observation.effort != 1.75) unreachable();
    if (observation.read_effort(size - 1)) unreachable();
    if (!observation.read_error_code(size) || observation.error_code != 257) unreachable();
    if (observation.read_error_code(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000600000100);
    writeWord(8, 0x000000656d617266);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x000000003fe00000);
    writeWord(32, 0x00000000bfd00000);
    writeByte(40, 0);
    writeByte(41, 0);
    writeByte(42, 252);
    writeByte(43, 63);
    writeByte(44, 1);
    writeByte(45, 1);
    check(46);
    writeWord(0, 0x0600000000000000);
    writeWord(8, 0x000000656d617266);
    writeWord(16, 0x0000e03f00000000);
    writeWord(24, 0x0000d0bf00000000);
    writeWord(32, 0x0000fc3f00000000);
    writeByte(40, 0);
    writeByte(41, 0);
    writeByte(42, 0);
    writeByte(43, 0);
    writeByte(44, 1);
    writeByte(45, 1);
    check(46);
}
