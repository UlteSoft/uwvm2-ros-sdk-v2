/** Read-only projections of fanuc_msgs/ForceSensor. */
/** Read force_x from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_force_x(data: Uint8Array): number | undefined;

/** Read force_z from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_force_z(data: Uint8Array): number | undefined;

/** Read moment_z from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_moment_z(data: Uint8Array): number | undefined;

/** Read fs_type from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_fs_type(data: Uint8Array): number | undefined;
