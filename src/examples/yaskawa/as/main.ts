import * as observation from "./uwrosv2/platform/yaskawa/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_number(size) || observation.number != 1027) unreachable();
    if (observation.read_number(size - 1)) unreachable();
    if (!observation.read_sub_code(size) || observation.sub_code != -2) unreachable();
    if (observation.read_sub_code(size - 1)) unreachable();
    if (!observation.read_datetime_sec(size) || observation.datetime_sec != -1) unreachable();
    if (observation.read_datetime_sec(size - 1)) unreachable();
    if (!observation.read_datetime_nanosec(size) || observation.datetime_nanosec != 1000) unreachable();
    if (observation.read_datetime_nanosec(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000040300000100);
    writeWord(8, 0x6d61726600000006);
    writeWord(16, 0xfffffffe00000065);
    writeWord(24, 0x000003e8ffffffff);
    check(32);
    writeWord(0, 0x0304000000000000);
    writeWord(8, 0x6d61726606000000);
    writeWord(16, 0xfeffffff00000065);
    writeWord(24, 0xe8030000ffffffff);
    check(32);
}
