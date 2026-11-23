import * as observation from "./uwrosv2/platform/universal_robots/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_status(size) || observation.status != 3) unreachable();
    if (observation.read_status(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeByte(0, 0);
    writeByte(1, 1);
    writeByte(2, 0);
    writeByte(3, 0);
    writeByte(4, 3);
    check(5);
    writeByte(0, 0);
    writeByte(1, 0);
    writeByte(2, 0);
    writeByte(3, 0);
    writeByte(4, 3);
    check(5);
}
