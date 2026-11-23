import * as observation from "./uwrosv2/platform/franka/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_position(size, 1) || observation.position != -1.0) unreachable();
    if (observation.read_position(size - 1, 1)) unreachable();
    if (observation.read_position(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_desired_position(size, 1) || observation.desired_position != 1.0) unreachable();
    if (observation.read_desired_position(size - 1, 1)) unreachable();
    if (observation.read_desired_position(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_commanded_position(size, 1) || observation.commanded_position != -1.0) unreachable();
    if (observation.read_commanded_position(size - 1, 1)) unreachable();
    if (observation.read_commanded_position(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_commanded_velocity(size, 1) || observation.commanded_velocity != -0.0625) unreachable();
    if (observation.read_commanded_velocity(size - 1, 1)) unreachable();
    if (observation.read_commanded_velocity(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_commanded_acceleration(size, 1) || observation.commanded_acceleration != -0.25) unreachable();
    if (observation.read_commanded_acceleration(size - 1, 1)) unreachable();
    if (observation.read_commanded_acceleration(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000000100);
    writeWord(8, 0x000000003ff20000);
    writeWord(16, 0x00000000bff00000);
    writeWord(24, 0x00000000bfe80000);
    writeWord(32, 0x000000003ff00000);
    writeWord(40, 0x000000003fd00000);
    writeWord(48, 0x00000000bff00000);
    writeWord(56, 0x000000003fa00000);
    writeWord(64, 0x00000000bfb00000);
    writeWord(72, 0x000000003fc00000);
    writeByte(80, 0);
    writeByte(81, 0);
    writeByte(82, 208);
    writeByte(83, 191);
    check(84);
    writeWord(0, 0x0000f23f00000000);
    writeWord(8, 0x0000f0bf00000000);
    writeWord(16, 0x0000e8bf00000000);
    writeWord(24, 0x0000f03f00000000);
    writeWord(32, 0x0000d03f00000000);
    writeWord(40, 0x0000f0bf00000000);
    writeWord(48, 0x0000a03f00000000);
    writeWord(56, 0x0000b0bf00000000);
    writeWord(64, 0x0000c03f00000000);
    writeWord(72, 0x0000d0bf00000000);
    writeByte(80, 0);
    writeByte(81, 0);
    writeByte(82, 0);
    writeByte(83, 0);
    check(84);
}
