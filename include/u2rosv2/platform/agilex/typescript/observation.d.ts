/** Read-only projections of scout_msgs/ScoutBmsStatus. */
/** Read soc from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_soc(data: Uint8Array): number | undefined;

/** Read battery_voltage from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_battery_voltage(data: Uint8Array): number | undefined;

/** Read battery_current from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_battery_current(data: Uint8Array): number | undefined;

/** Read alarm_status_1 from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_alarm_status_1(data: Uint8Array): number | undefined;
