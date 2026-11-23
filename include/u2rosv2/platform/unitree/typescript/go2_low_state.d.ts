/** Encode the six little-endian u64 words in a Go2 buffer.read submission. */
export declare function encode_read(sequence: bigint, deadlineNs: bigint): Uint8Array;
/** Read the tick and finite first joint position. An invalid driver.result returns undefined. */
export declare function decode_result(frame: Uint8Array): {tick: number; first_joint_position: number} | undefined;
