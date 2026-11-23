import * as observation from "./uwrosv2/platform/clearpath/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_state(size) || observation.state != 3) unreachable();
    if (observation.read_state(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeByte(0, 3);
    check(1);
}
