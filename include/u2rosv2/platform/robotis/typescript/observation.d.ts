/** Read-only projections of turtlebot3_msgs/SensorState. */
export declare const BUMPER_FORWARD: 1;
export declare const BUMPER_BACKWARD: 2;
export declare const CLIFF: 1;
export declare const SONAR: 1;
export declare const ILLUMINATION: 1;
export declare const BUTTON0: 1;
export declare const BUTTON1: 2;
export declare const ERROR_LEFT_MOTOR: 1;
export declare const ERROR_RIGHT_MOTOR: 2;
export declare const TORQUE_ON: 1;
export declare const TORQUE_OFF: 2;
/** Read bumper from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_bumper(data: Uint8Array): number | undefined;

/** Read left_encoder from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_left_encoder(data: Uint8Array): number | undefined;

/** Read right_encoder from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_right_encoder(data: Uint8Array): number | undefined;

/** Read battery from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_battery(data: Uint8Array): number | undefined;
