/** Read-only projections of simulator_pub_msg. */
/** Read timestamp from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_timestamp(data: Uint8Array): bigint | undefined;

/** Read q from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_q(data: Uint8Array, index: number): number | undefined;

/** Read q_dot from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_q_dot(data: Uint8Array, index: number): number | undefined;

/** Read lf_touch from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_lf_touch(data: Uint8Array): number | undefined;

/** Read rf_touch from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_rf_touch(data: Uint8Array): number | undefined;
