/** Read-only projections of pal_device_msgs/BatteryState. */
export declare const FULL: 5;
export declare const HIGH: 4;
export declare const MEDIUM: 3;
export declare const LOW: 2;
export declare const CRITICAL_LOW: 1;
/** Read charge_state from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_charge_state(data: Uint8Array): number | undefined;

/** Read battery_percentage from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_battery_percentage(data: Uint8Array): number | undefined;
