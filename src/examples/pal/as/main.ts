import * as observation from "./uwrosv2/platform/pal/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_charge_state(size) || observation.charge_state != 3) unreachable();
    if (observation.read_charge_state(size - 1)) unreachable();
    if (!observation.read_battery_percentage(size) || observation.battery_percentage != 67.5) unreachable();
    if (observation.read_battery_percentage(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeByte(0, 3);
    writeByte(1, 0);
    writeByte(2, 0);
    writeByte(3, 135);
    writeByte(4, 66);
    check(5);
}
