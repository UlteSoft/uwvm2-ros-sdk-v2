import * as observation from "./uwrosv2/platform/kinova/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_feedback_id_identifier(size) || observation.feedback_id_identifier != 1234) unreachable();
    if (observation.read_feedback_id_identifier(size - 1)) unreachable();
    if (!observation.read_jitter_comm(size) || observation.jitter_comm != 150) unreachable();
    if (observation.read_jitter_comm(size - 1)) unreachable();
    if (!observation.read_voltage(size) || observation.voltage != 47.5) unreachable();
    if (observation.read_voltage(size - 1)) unreachable();
    if (!observation.read_temperature_motor(size) || observation.temperature_motor != 42.25) unreachable();
    if (observation.read_temperature_motor(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x00000000000004d2);
    writeWord(8, 0x0000000000000096);
    writeWord(16, 0x0000000000000000);
    writeWord(24, 0x423e000000000000);
    writeWord(32, 0x0000000042290000);
    writeWord(40, 0x0000000000000000);
    writeWord(48, 0x0000000000000000);
    check(56);
}
