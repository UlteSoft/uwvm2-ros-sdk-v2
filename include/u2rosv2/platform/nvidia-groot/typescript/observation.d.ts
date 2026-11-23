/** Read-only projections of DROID observation.state. */
/** Read eef_9d from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_eef_9d(data: Uint8Array, index: number): number | undefined;

/** Read gripper_position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_gripper_position(data: Uint8Array): number | undefined;

/** Read joint_position from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_joint_position(data: Uint8Array, index: number): number | undefined;
