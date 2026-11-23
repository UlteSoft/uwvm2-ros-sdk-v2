import * as observation from "./uwrosv2/platform/kuka/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_cycle_time(size) || observation.cycle_time != 2) unreachable();
    if (observation.read_cycle_time(size - 1)) unreachable();
    if (!observation.read_drives_powered(size) || observation.drives_powered != true) unreachable();
    if (observation.read_drives_powered(size - 1)) unreachable();
    if (!observation.read_guard_stop(size) || observation.guard_stop != false) unreachable();
    if (observation.read_guard_stop(size - 1)) unreachable();
    if (!observation.read_operation_mode(size) || observation.operation_mode != 3) unreachable();
    if (observation.read_operation_mode(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0001020000000100);
    writeByte(8, 0);
    writeByte(9, 0);
    writeByte(10, 0);
    writeByte(11, 3);
    writeByte(12, 0);
    check(13);
    writeWord(0, 0x0001020000000000);
    writeByte(8, 0);
    writeByte(9, 0);
    writeByte(10, 0);
    writeByte(11, 3);
    writeByte(12, 0);
    check(13);
}
