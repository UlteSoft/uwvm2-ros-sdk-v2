import * as observation from "./uwrosv2/platform/hello_robot/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_ax(size) || observation.ax != 0.5) unreachable();
    if (observation.read_ax(size - 1)) unreachable();
    if (!observation.read_az(size) || observation.az != 9.5) unreachable();
    if (observation.read_az(size - 1)) unreachable();
    if (!observation.read_a0(size) || observation.a0 != -120) unreachable();
    if (observation.read_a0(size - 1)) unreachable();
    if (!observation.read_single_tap_count(size) || observation.single_tap_count != 513) unreachable();
    if (observation.read_single_tap_count(size - 1)) unreachable();
    if (!observation.read_timestamp(size) || observation.timestamp != 305419896) unreachable();
    if (observation.read_timestamp(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x000000003f000000);
    writeWord(8, 0x0000ff8841180000);
    writeWord(16, 0x0000000002010000);
    writeWord(24, 0x0000123456780000);
    writeByte(32, 0);
    writeByte(33, 0);
    check(34);
}
