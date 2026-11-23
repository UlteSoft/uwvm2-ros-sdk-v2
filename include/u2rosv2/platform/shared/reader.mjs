/** Project a numeric field after validating the complete source-pinned observation record. */
const widths = {bool: 1, u8: 1, i8: 1, u16: 2, i16: 2, u32: 4, i32: 4, f32: 4,
                u64: 8, i64: 8, f64: 8, str: 0};

function scalar(view, at, type, little) {
    switch (type) {
        case "bool": return view.getUint8(at) !== 0;
        case "u8": return view.getUint8(at);
        case "i8": return view.getInt8(at);
        case "u16": return view.getUint16(at, little);
        case "i16": return view.getInt16(at, little);
        case "u32": return view.getUint32(at, little);
        case "i32": return view.getInt32(at, little);
        case "u64": return view.getBigUint64(at, little);
        case "i64": return view.getBigInt64(at, little);
        case "f32": return view.getFloat32(at, little);
        case "f64": return view.getFloat64(at, little);
    }
}

export function project(data, format, fields, wanted, index) {
    if (!(data instanceof Uint8Array) || !Number.isSafeInteger(index) || index < 0) return undefined;
    const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
    const cdr = format === 1 || (format === 3 && data.length !== 32);
    let base = 0, tail = 0, little = true;
    if (cdr) {
        if (data.length < 4 || data[0] !== 0 || data[1] > 1 || data[2] !== 0 || data[3] > 3) return undefined;
        base = 4;
        little = data[1] === 1;
        tail = data[3];
    } else if (format === 2) {
        if (data.length < 8 || view.getBigUint64(0, false) !== 0x4abec52f17edd11fn) return undefined;
        base = 8;
        little = false;
    }
    let pos = 0, saved = 0, result;
    const size = data.length - base;
    function take(count, width) {
        const start = pos + (cdr ? (width - pos % width) % width : 0);
        if (count > Math.floor((size - start) / width)) return -1;
        pos = start + count * width;
        return base + start;
    }
    function count32() {
        const at = take(1, 4);
        return at < 0 ? -1 : view.getUint32(at, little);
    }
    for (let i = 0; i < fields.length; ++i) {
        const [type, repeat, kind] = fields[i];
        const width = widths[type];
        let count = repeat;
        if (repeat === 0) count = count32();
        if (repeat === -1) count = saved;
        if (repeat < -1) {
            if ((size - pos) % ((-1 - repeat) * width) !== 0) return undefined;
            count = (size - pos) / width;
        }
        if (count < 0) return undefined;
        if (type === "str") {
            if (count > Math.floor((size - pos) / 4)) return undefined;
            for (let j = 0; j < count; ++j) {
                const length = count32();
                if (length < 0) return undefined;
                const at = take(length, 1);
                if (at < 0 || (cdr && (length === 0 || data[at + length - 1] !== 0))) return undefined;
            }
        } else if (count > 0) {
            const at = take(count, width);
            if (at < 0) return undefined;
            if (kind === 2) {
                saved = view.getUint32(at, little);
                if (saved > 0x7fffffff) return undefined;
            }
            if (kind === 1) {
                for (let j = 0; j < count; ++j) if (data[at + j] > 1) return undefined;
            }
            if (i === wanted && index < count) result = scalar(view, at + index * width, type, little);
        }
    }
    const left = size - pos;
    if ((left !== 0 && left !== tail) || (tail !== 0 && tail !== (4 - pos % 4) % 4)) return undefined;
    return result;
}
