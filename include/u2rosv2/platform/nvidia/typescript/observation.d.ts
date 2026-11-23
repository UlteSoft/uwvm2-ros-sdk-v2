/** Read-only projections of isaac_ros_nova_interfaces/EncoderTicks. */
/** Read left_ticks from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_left_ticks(data: Uint8Array): number | undefined;

/** Read right_ticks from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_right_ticks(data: Uint8Array): number | undefined;

/** Read encoder_timestamp from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_encoder_timestamp(data: Uint8Array): bigint | undefined;
