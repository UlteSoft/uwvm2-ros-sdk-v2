import * as observation from "./uwrosv2/platform/deep_robotics/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_roll(size) || observation.roll != 0.25) unreachable();
    if (observation.read_roll(size - 1)) unreachable();
    if (!observation.read_yaw(size) || observation.yaw != -0.75) unreachable();
    if (observation.read_yaw(size - 1)) unreachable();
    if (!observation.read_omega_z(size) || observation.omega_z != 1.5) unreachable();
    if (observation.read_omega_z(size - 1)) unreachable();
    if (!observation.read_acc_z(size) || observation.acc_z != 9.5) unreachable();
    if (observation.read_acc_z(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x3e80000000000100);
    writeWord(8, 0xbf40000000000000);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x000000003fc00000);
    writeWord(32, 0x4118000000000000);
    check(40);
    writeWord(0, 0x0000803e00000000);
    writeWord(8, 0x000040bf00000000);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x000000000000c03f);
    writeWord(32, 0x0000184100000000);
    check(40);
}
