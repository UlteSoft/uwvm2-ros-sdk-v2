/** Read-only projections of booster_interface/ImuState. */
/** Read rpy from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_rpy(data: Uint8Array, index: number): number | undefined;

/** Read gyro from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_gyro(data: Uint8Array, index: number): number | undefined;

/** Read acc from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_acc(data: Uint8Array, index: number): number | undefined;
