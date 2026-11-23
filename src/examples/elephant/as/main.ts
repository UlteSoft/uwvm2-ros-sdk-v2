import * as observation from "./uwrosv2/platform/elephant/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_status(size) || observation.status != true) unreachable();
    if (observation.read_status(size - 1)) unreachable();
    if (!observation.read_pin1(size) || observation.pin1 != -1) unreachable();
    if (observation.read_pin1(size - 1)) unreachable();
    if (!observation.read_pin2(size) || observation.pin2 != 2) unreachable();
    if (observation.read_pin2(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeByte(0, 1);
    writeByte(1, 255);
    writeByte(2, 2);
    check(3);
}
