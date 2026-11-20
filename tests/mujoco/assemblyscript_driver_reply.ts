/** @file assemblyscript_driver_reply.ts
 * @brief Exercise short-reply preflight and exact result retry over TLS.
 */
import { writeByte, writeWord, open, opened, connect, submit, result,
         resultWithCapacity, disconnect, replySize, replyRequired,
         clearReply, readWord } from "./wros";

export function _start(): void {
    writeWord(0, 0x656772616c); // "large"
    if (open(5) != 0) unreachable();
    const driver = opened();
    let status: u32 = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = connect(driver);
    if (status != 0) unreachable();

    stageRequest();
    writeWord(0, 1);
    status = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) status = submit(driver, REQUEST_BYTES);
    if (status != 0) unreachable();

    if (result(driver, 1) != 90 || replySize() != 0 || replyRequired() != REQUIRED) unreachable();
    if (resultWithCapacity(driver, 1, REQUIRED - 1) != 90 ||
        replySize() != 0 || replyRequired() != REQUIRED) unreachable();

    status = 11;
    for (let attempt = 0; status == 11 && attempt < 10000000; ++attempt) {
        status = resultWithCapacity(driver, 1, REQUIRED);
    }
    if (status != 0 || replyRequired() != 0 || replySize() != 16 + RESULT_BYTES) unreachable();
    if (readWord(0) != 0 || readWord(8) != RESULT_BYTES || readWord(16) != 1) unreachable();
    if (readWord(24) != 5 || readWord(37) != 5 || readWord(45) != LARGE_BYTES) unreachable();
    if (readWord(53) != 0x5252525252525252 || readWord(741) != 0x5252525252525252) unreachable();
    if (readWord(753) != 1 || readWord(761) != 42) unreachable();

    clearReply();
    if (replySize() != 0 || replyRequired() != 0 || readWord(0) != 0) unreachable();
    if (resultWithCapacity(driver, 1, REQUIRED) != 11 || replySize() != 0) unreachable();
    if (disconnect(driver) != 0) unreachable();
}
