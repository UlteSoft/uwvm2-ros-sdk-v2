import { encode_read, decode_result, tick, first_joint_position } from "./uwrosv2/platform/unitree/go2_low_state";
import { readRequestByte, writeWord } from "./wros";

export function _start(): void {
    encode_read(7, 1000);
    if (readRequestByte(40) != 16) unreachable();
    writeWord(0, 0);
    writeWord(8, 24);
    writeWord(16, 16);
    writeWord(24, 41347);
    writeWord(32, 0x3e000000);
    if (!decode_result(40) || tick != 41347 || first_joint_position != 0.125) unreachable();
    if (decode_result(39)) unreachable();
    writeWord(32, 0x7f800000);
    if (decode_result(40)) unreachable();
}
