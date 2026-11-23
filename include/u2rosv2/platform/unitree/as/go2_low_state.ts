/** Codec for the Go2 driver envelope in the bounded AssemblyScript staging area. */
import { readRequestByte, readWord, replySize, writeWord } from "../../../wros";

/** Stage the six little-endian u64 words for a read-only Go2 submission. */
export function encode_read(sequence: u64, deadlineNs: u64): void {
    writeWord(0, sequence);
    writeWord(8, deadlineNs);
    writeWord(16, 24);
    writeWord(24, 1);
    writeWord(32, 0);
    writeWord(40, 16);
}

export let tick: u32 = 0;
export let first_joint_position: f32 = 0;

function word(offset: u32, fromReply: bool): u64 {
    if (fromReply) return readWord(offset);
    let value: u64 = 0;
    for (let i: u32 = 0; i < 8; ++i) value |= <u64>readRequestByte(offset + i) << (8 * i);
    return value;
}

/** Validate the complete 40-byte result, then publish both fields together. */
export function decode_result(size: u32, fromReply: bool = false): bool {
    if (size != 40 || (fromReply && replySize() != size) || word(0, fromReply) != 0 ||
        word(8, fromReply) != 24 || word(16, fromReply) != 16) return false;
    const time = word(24, fromReply), position = word(32, fromReply);
    if (time > u32.MAX_VALUE || position > u32.MAX_VALUE || (<u32>position & 0x7f800000) == 0x7f800000) return false;
    tick = <u32>time;
    first_joint_position = reinterpret<f32>(<u32>position);
    return true;
}
