/** Encode the six little-endian u64 words in a Go2 buffer.read submission. */
export function encode_read(sequence, deadlineNs) {
    for (const value of [sequence, deadlineNs]) {
        if (typeof value !== "bigint" || value < 0n || value > 0xffffffffffffffffn) throw RangeError("expected u64");
    }
    const data = new Uint8Array(48), view = new DataView(data.buffer);
    [sequence, deadlineNs, 24n, 1n, 0n, 16n].forEach((word, i) => view.setBigUint64(i * 8, word, true));
    return data;
}

/** Read a complete successful driver.result, including the finite binary32 joint position. */
export function decode_result(frame) {
    if (!(frame instanceof Uint8Array) || frame.byteLength !== 40) return undefined;
    const view = new DataView(frame.buffer, frame.byteOffset, frame.byteLength);
    if (view.getBigUint64(0, true) !== 0n || view.getBigUint64(8, true) !== 24n ||
        view.getBigUint64(16, true) !== 16n || view.getUint32(28, true) !== 0 ||
        view.getUint32(36, true) !== 0) return undefined;
    const position = view.getFloat32(32, true);
    return Number.isFinite(position) ? {tick: view.getUint32(24, true), first_joint_position: position} : undefined;
}
