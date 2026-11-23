import * as observation from "./uwrosv2/platform/realman/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_joint_error(size, 1) || observation.joint_error != 258) unreachable();
    if (observation.read_joint_error(size - 1, 1)) unreachable();
    if (observation.read_joint_error(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_dof(size) || observation.dof != 2) unreachable();
    if (observation.read_dof(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000200000100);
    writeByte(8, 0);
    writeByte(9, 0);
    writeByte(10, 2);
    writeByte(11, 1);
    writeByte(12, 2);
    check(13);
    writeWord(0, 0x0200000000000000);
    writeByte(8, 0);
    writeByte(9, 0);
    writeByte(10, 1);
    writeByte(11, 2);
    writeByte(12, 2);
    check(13);
}
