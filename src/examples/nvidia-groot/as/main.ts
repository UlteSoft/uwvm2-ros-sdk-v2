import * as observation from "./uwrosv2/platform/nvidia-groot/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_eef_9d(size, 1) || observation.eef_9d != 0.125) unreachable();
    if (observation.read_eef_9d(size - 1, 1)) unreachable();
    if (observation.read_eef_9d(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_gripper_position(size) || observation.gripper_position != 0.75) unreachable();
    if (observation.read_gripper_position(size - 1)) unreachable();
    if (!observation.read_joint_position(size, 1) || observation.joint_position != -0.25) unreachable();
    if (observation.read_joint_position(size - 1, 1)) unreachable();
    if (observation.read_joint_position(size, u32.MAX_VALUE)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x3e00000000000000);
    writeWord(8, 0x0000000000000000);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x0000000000000000);
    writeWord(32, 0x3f40000000000000);
    writeWord(40, 0xbe80000000000000);
    writeWord(48, 0x0000000000000000);
    writeWord(56, 0x0000000000000000);
    writeByte(64, 0);
    writeByte(65, 0);
    writeByte(66, 0);
    writeByte(67, 0);
    check(68);
}
