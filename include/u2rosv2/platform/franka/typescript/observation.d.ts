/** Read-only projections of franka_msgs/Elbow. */
/** Read position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_position(data: Uint8Array, index: number): number | undefined;

/** Read desired_position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_desired_position(data: Uint8Array, index: number): number | undefined;

/** Read commanded_position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_commanded_position(data: Uint8Array, index: number): number | undefined;

/** Read commanded_velocity from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_commanded_velocity(data: Uint8Array, index: number): number | undefined;

/** Read commanded_acceleration from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_commanded_acceleration(data: Uint8Array, index: number): number | undefined;
