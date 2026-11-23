/** Read-only projections of kuavo_msgs/BatteryInfo. */
/** Read voltage from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_voltage(data: Uint8Array): number | undefined;

/** Read current from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_current(data: Uint8Array): number | undefined;

/** Read percentage from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_percentage(data: Uint8Array): number | undefined;

/** Read temperatures from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_temperatures(data: Uint8Array, index: number): number | undefined;
