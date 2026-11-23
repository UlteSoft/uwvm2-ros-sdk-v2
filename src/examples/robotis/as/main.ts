import * as observation from "./uwrosv2/platform/robotis/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_bumper(size) || observation.bumper != 3) unreachable();
    if (observation.read_bumper(size - 1)) unreachable();
    if (!observation.read_left_encoder(size) || observation.left_encoder != -105) unreachable();
    if (observation.read_left_encoder(size - 1)) unreachable();
    if (!observation.read_right_encoder(size) || observation.right_encoder != 300) unreachable();
    if (observation.read_right_encoder(size - 1)) unreachable();
    if (!observation.read_battery(size) || observation.battery != 12.25) unreachable();
    if (observation.read_battery(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000000);
    writeWord(8, 0x0000000500000000);
    writeWord(16, 0x000003656d617266);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0xffff970000000000);
    writeWord(40, 0x4400000000012cff);
    writeByte(48, 65);
    check(49);
}
