import * as observation from "./uwrosv2/platform/dobot/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_is_enable(size) || observation.is_enable != false) unreachable();
    if (observation.read_is_enable(size - 1)) unreachable();
    if (!observation.read_is_connected(size) || observation.is_connected != true) unreachable();
    if (observation.read_is_connected(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeByte(0, 0);
    writeByte(1, 1);
    writeByte(2, 0);
    writeByte(3, 0);
    writeByte(4, 0);
    writeByte(5, 1);
    check(6);
    writeByte(0, 0);
    writeByte(1, 0);
    writeByte(2, 0);
    writeByte(3, 0);
    writeByte(4, 0);
    writeByte(5, 1);
    check(6);
}
