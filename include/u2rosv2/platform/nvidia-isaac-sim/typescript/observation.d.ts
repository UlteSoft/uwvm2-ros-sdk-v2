/** Read-only projections of Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock. */
/** Read clock_sec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_clock_sec(data: Uint8Array): number | undefined;

/** Read clock_nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_clock_nanosec(data: Uint8Array): number | undefined;
