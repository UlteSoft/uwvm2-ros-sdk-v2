/** Read-only projections of builtin_interfaces/Duration. */
/** Read sec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_sec(data: Uint8Array): number | undefined;

/** Read nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_nanosec(data: Uint8Array): number | undefined;
