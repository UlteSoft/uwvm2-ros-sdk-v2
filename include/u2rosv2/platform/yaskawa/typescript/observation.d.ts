/** Read-only projections of motoros2_interfaces/ErrorInfo. */
/** Read number from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_number(data: Uint8Array): number | undefined;

/** Read sub_code from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_sub_code(data: Uint8Array): number | undefined;

/** Read datetime_sec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_datetime_sec(data: Uint8Array): number | undefined;

/** Read datetime_nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_datetime_nanosec(data: Uint8Array): number | undefined;
