/** Read-only projections of drdds/ImuDataValue. */
/** Read roll from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_roll(data: Uint8Array): number | undefined;

/** Read yaw from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_yaw(data: Uint8Array): number | undefined;

/** Read omega_z from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_omega_z(data: Uint8Array): number | undefined;

/** Read acc_z from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_acc_z(data: Uint8Array): number | undefined;
