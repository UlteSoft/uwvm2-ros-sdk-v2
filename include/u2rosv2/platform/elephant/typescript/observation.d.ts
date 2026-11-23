/** Read-only projections of myarm_communication/MyArmPumpStatus. */
/** Read status from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_status(data: Uint8Array): boolean | undefined;

/** Read pin1 from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_pin1(data: Uint8Array): number | undefined;

/** Read pin2 from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_pin2(data: Uint8Array): number | undefined;
