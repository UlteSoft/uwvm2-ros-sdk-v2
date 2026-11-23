/** Scalar cursor over the bounded request staging area or the last successful driver reply. */
import { readRequestByte, readReplyByte, replySize } from "../../wros";

let reply: bool = false, cdr: bool = false, big: bool = false, found: bool = false;
let base: u32 = 0, size: u32 = 0, pos: u32 = 0, tail: u32 = 0, saved: u32 = 0;
export let bits: u64 = 0;

function octet(at: u32): u32 {
    return reply ? readReplyByte(base + at) : readRequestByte(base + at);
}
function word(at: u32, width: u32): u64 {
    let value: u64 = 0;
    for (let i: u32 = 0; i < width; ++i) {
        const shift = (big ? width - 1 - i : i) * 8;
        value |= <u64>octet(at + i) << shift;
    }
    return value;
}

export function begin(format: u32, length: u32, fromReply: bool): bool {
    if (length > (fromReply ? replySize() : 512)) return false;
    reply = fromReply; size = length; base = 0; pos = 0; tail = 0; saved = 0; found = false;
    cdr = format == 1 || (format == 3 && size != 32);
    big = format == 2;
    if (cdr) {
        if (size < 4 || octet(0) != 0 || octet(1) > 1 || octet(2) != 0 || octet(3) > 3) return false;
        big = octet(1) == 0;
        tail = octet(3);
        base = 4;
    } else if (big) {
        if (size < 8 || word(0, 8) != 0x4abec52f17edd11f) return false;
        base = 8;
    }
    size -= base;
    return true;
}

function take(count: u32, width: u32): i32 {
    const at = pos + (cdr ? ((0 - pos) & (width - 1)) : 0);
    if (at > size || count > (size - at) / width) return -1;
    pos = at + count * width;
    return <i32>at;
}
function count32(): i64 {
    const at = take(1, 4);
    return at < 0 ? -1 : <i64>word(<u32>at, 4);
}

export function field(width: u32, repeat: i32, kind: u32, wanted: bool, index: u32): bool {
    let count: u32;
    if (repeat == 0) {
        const length = count32();
        if (length < 0) return false;
        count = <u32>length;
    } else if (repeat == -1) {
        count = saved;
    } else if (repeat < -1) {
        if ((size - pos) % (<u32>(-1 - repeat) * width) != 0) return false;
        count = (size - pos) / width;
    } else {
        count = <u32>repeat;
    }
    if (width == 0) {
        if (count > (size - pos) / 4) return false;
        for (let j: u32 = 0; j < count; ++j) {
            const length = count32();
            if (length < 0) return false;
            const at = take(<u32>length, 1);
            if (at < 0 || (cdr && (length == 0 || octet(<u32>at + <u32>length - 1) != 0))) return false;
        }
    } else if (count > 0) {
        const at = take(count, width);
        if (at < 0) return false;
        if (kind == 2) {
            saved = <u32>word(<u32>at, width);
            if (saved > 0x7fffffff) return false;
        } else if (kind == 1) {
            for (let j: u32 = 0; j < count; ++j) if (octet(<u32>at + j) > 1) return false;
        }
        if (wanted && index < count) {
            bits = word(<u32>at + index * width, width);
            found = true;
        }
    }
    return true;
}

export function finish(): bool {
    const left = size - pos;
    return found && (left == 0 || left == tail) && (tail == 0 || tail == ((0 - pos) & 3));
}
