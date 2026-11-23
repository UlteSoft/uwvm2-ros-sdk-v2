/** Read-only projections of dsr_msgs/LogAlarm. */
/** Read level from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_level(data: Uint8Array): number | undefined;

/** Read group from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_group(data: Uint8Array): number | undefined;

/** Read index from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_index(data: Uint8Array): number | undefined;
