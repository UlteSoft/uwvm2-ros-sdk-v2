/** Read-only projections of kuka_driver_interfaces/KssStatus. */
export declare const UNSPECIFIED: 0;
export declare const JOINT_POSITION_CONTROL: 1;
export declare const CARTESIAN_POSITION_CONTROL: 5;
export declare const RSI_4MS: 1;
export declare const RSI_12MS: 2;
export declare const T1: 1;
export declare const T2: 2;
export declare const AUT: 3;
export declare const EXT: 4;
/** Read cycle_time from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_cycle_time(data: Uint8Array): number | undefined;

/** Read drives_powered from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_drives_powered(data: Uint8Array): boolean | undefined;

/** Read guard_stop from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_guard_stop(data: Uint8Array): boolean | undefined;

/** Read operation_mode from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_operation_mode(data: Uint8Array): number | undefined;
