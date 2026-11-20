/** @file assemblyscript_driver.ts
 * @brief Check direct ROSv2 driver results from a fixed-size AssemblyScript frame.
 */
import { writeByte, writeWord, open, opened, connect, submit, result,
         describe, disconnect, replySize, readWord } from "./wros";

export function _start(): void {
    writeWord(0, 0x746e696f6a); // "joint"
    if (open(5) != 0) unreachable();
    const joint = opened();
    let status: u32 = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = connect(joint);
    if (status != 0) unreachable();
    stageRequest();
    for (let sequence: u64 = 1; sequence <= STEPS; ++sequence) {
        writeWord(0, sequence);
        writeWord(32, sequence);
        if (MODE == 0) writeWord(TARGET, (sequence & 1) != 0 ? 0x3fe0000000000000 : 0xbfe0000000000000);
        status = 11;
        for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) {
            status = submit(joint, REQUEST_BYTES);
        }
        if (status != 0) unreachable();
        status = 11;
        for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = result(joint);
        if (MODE == 2) {
            if ((status != 5 && status != 13) || replySize() != 0) unreachable();
            if (describe(joint) != 0 || replySize() < 32 || readWord(0) != 6 || readWord(24) != 1) unreachable();
        } else if (status != 0 || replySize() < 24 || readWord(0) != (MODE == 1 ? 13 : 0) || readWord(16) != sequence) {
            unreachable();
        }
    }
    if (disconnect(joint) != 0) unreachable();
}
