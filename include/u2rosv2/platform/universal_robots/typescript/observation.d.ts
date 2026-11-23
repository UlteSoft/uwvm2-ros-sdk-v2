/** Read-only projections of ur_dashboard_msgs/SafetyStatus. */
export declare const NORMAL: 1;
export declare const REDUCED: 2;
export declare const PROTECTIVE_STOP: 3;
export declare const RECOVERY: 4;
export declare const SAFEGUARD_STOP: 5;
export declare const SYSTEM_EMERGENCY_STOP: 6;
export declare const ROBOT_EMERGENCY_STOP: 7;
export declare const VIOLATION: 8;
export declare const FAULT: 9;
export declare const VALIDATE_JOINT_ID: 10;
export declare const UNDEFINED_SAFETY_MODE: 11;
export declare const AUTOMATIC_MODE_SAFEGUARD_STOP: 12;
export declare const SYSTEM_THREE_POSITION_ENABLING_STOP: 13;
export declare const TP_THREE_POSITION_ENABLING_STOP: 14;
export declare const IMMI_EMERGENCY_STOP: 15;
export declare const IMMI_SAFEGUARD_STOP: 16;
export declare const PROFISAFE_WAITING_FOR_PARAMETERS: 17;
export declare const PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP: 18;
export declare const PROFISAFE_SAFEGUARD_STOP: 19;
export declare const PROFISAFE_EMERGENCY_STOP: 20;
export declare const SAFETY_API_SAFEGUARD_STOP: 22;
export declare const IO_PLANE_STOP: 23;
/** Read status from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_status(data: Uint8Array): number | undefined;
