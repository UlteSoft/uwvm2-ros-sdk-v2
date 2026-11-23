/** Read-only projections of clearpath_dock_msgs/DockState. */
export declare const UNDOCKED: 0;
export declare const DOCKED: 1;
export declare const IN_PROGRESS: 2;
export declare const FAILED: 3;
export declare const CANCELLED: 4;
/** Read state from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_state(data: Uint8Array): number | undefined;
