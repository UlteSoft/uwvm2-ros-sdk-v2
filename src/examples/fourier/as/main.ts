import * as observation from "./uwrosv2/platform/fourier/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_timestamp(size) || observation.timestamp != 4294967302) unreachable();
    if (observation.read_timestamp(size - 1)) unreachable();
    if (!observation.read_q(size, 1) || observation.q != -0.125) unreachable();
    if (observation.read_q(size - 1, 1)) unreachable();
    if (observation.read_q(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_q_dot(size, 1) || observation.q_dot != 0.5) unreachable();
    if (observation.read_q_dot(size - 1, 1)) unreachable();
    if (observation.read_q_dot(size, u32.MAX_VALUE)) unreachable();
    if (!observation.read_lf_touch(size) || observation.lf_touch != 0.25) unreachable();
    if (observation.read_lf_touch(size - 1)) unreachable();
    if (!observation.read_rf_touch(size) || observation.rf_touch != 0.75) unreachable();
    if (observation.read_rf_touch(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x1fd1ed172fc5be4a);
    writeWord(8, 0x0600000001000000);
    writeWord(16, 0x0000000002000000);
    writeWord(24, 0x0000c0bf00000000);
    writeWord(32, 0x0000000000000000);
    writeWord(40, 0x0000e03f00000000);
    writeWord(48, 0x0000000000000000);
    writeWord(56, 0x0000000000000000);
    writeWord(64, 0x0000000000000000);
    writeWord(72, 0x0000000000000000);
    writeWord(80, 0x0000000000000000);
    writeWord(88, 0x0000000000000000);
    writeWord(96, 0x0000000000000000);
    writeWord(104, 0x0000000000000000);
    writeWord(112, 0x0000000000000000);
    writeWord(120, 0x0000000000000000);
    writeWord(128, 0x0000d03f00000000);
    writeWord(136, 0x0000e83f00000000);
    writeWord(144, 0x0000000000000000);
    writeWord(152, 0x0000000000000000);
    writeWord(160, 0x0000000000000000);
    writeWord(168, 0x0000000000000000);
    writeWord(176, 0x0000000000000000);
    writeWord(184, 0x0000000000000000);
    writeByte(192, 0);
    writeByte(193, 0);
    writeByte(194, 0);
    writeByte(195, 0);
    check(196);
}
