/** Read-only projections of kortex_driver/ActuatorCyclic_Feedback. */
/** Read feedback_id_identifier from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_feedback_id_identifier(data: Uint8Array): number | undefined;

/** Read jitter_comm from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_jitter_comm(data: Uint8Array): number | undefined;

/** Read voltage from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_voltage(data: Uint8Array): number | undefined;

/** Read temperature_motor from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_temperature_motor(data: Uint8Array): number | undefined;
