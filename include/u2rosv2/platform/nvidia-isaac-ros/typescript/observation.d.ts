/** Read-only projections of isaac_ros_tensor_list_interfaces/TensorShape. */
/** Read rank from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_rank(data: Uint8Array): number | undefined;

/** Read dims from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_dims(data: Uint8Array, index: number): number | undefined;
