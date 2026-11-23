import * as observation from "./uwrosv2/platform/fanuc/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_force_x(size) || observation.force_x != -2.5) unreachable();
    if (observation.read_force_x(size - 1)) unreachable();
    if (!observation.read_force_z(size) || observation.force_z != 8.25) unreachable();
    if (observation.read_force_z(size - 1)) unreachable();
    if (!observation.read_moment_z(size) || observation.moment_z != -0.125) unreachable();
    if (observation.read_moment_z(size - 1)) unreachable();
    if (!observation.read_fs_type(size) || observation.fs_type != 2) unreachable();
    if (observation.read_fs_type(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0xc020000000000100);
    writeWord(8, 0x4104000000000000);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x00000002be000000);
    check(32);
    writeWord(0, 0x000020c000000000);
    writeWord(8, 0x0000044100000000);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x02000000000000be);
    check(32);
}
