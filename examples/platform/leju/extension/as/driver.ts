/** @file driver.ts
 *  @brief Verify the selected platform's driver grant and extension checks.
 */
import { close, connect, open, opened, replyRequired, replySize, writeWord } from "./wros";

export function _start(): void {
    writeWord(0, 0x6d7261); // "arm"
    if (open(3) != 0) unreachable();
    const handle = opened();
    if (handle == 0 || connect(handle) != 13) unreachable();
    if (replySize() != 0 || replyRequired() != 0) unreachable();
    if (close(handle) != 0 || opened() != 0) unreachable();
}
