/** Read-only projections of aimdk_msgs/JointState. */
/** Read position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_position(data: Uint8Array): number | undefined;

/** Read velocity from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_velocity(data: Uint8Array): number | undefined;

/** Read effort from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_effort(data: Uint8Array): number | undefined;

/** Read error_code from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_error_code(data: Uint8Array): number | undefined;
