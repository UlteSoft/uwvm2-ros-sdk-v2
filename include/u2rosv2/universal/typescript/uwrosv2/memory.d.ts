/**
 * Read the guest address of the first byte of an attached ArrayBuffer. Keep both the buffer
 * and its contents valid through the synchronous call. For operations that retain a region,
 * keep the buffer reachable and attached until the corresponding release or acknowledgement.
 * A zero-length buffer has no addressable bytes. Its address may be zero or a VM-specific
 * non-dereferenceable value; pass 0n for an empty range when the operation permits it.
 * Use a separate writable eight-byte buffer for the little-endian result length.
 * @param buffer - Guest-owned storage. Address the backing buffer of a typed array
 * and add BigInt(view.byteOffset) when passing a view that starts partway through the buffer.
 * @returns The guest's unsigned pointer bits, including any WasmMTE tag.
 */
export declare function addressOf(buffer: ArrayBuffer): bigint;
