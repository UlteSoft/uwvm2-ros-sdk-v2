//! Message records generated from the dashboard package registered by the UR ROS 2 driver.
//! Each string borrows its input bytes. The CDR codec accepts either byte order.
const cdr = @import("cdr.zig");

pub const Endian = cdr.Endian;
pub const Error = cdr.Error;

/// `ur_dashboard_msgs/msg/OperationalMode`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/OperationalMode.msg
pub const OperationalMode = struct {
    /// Dashboard operational mode, such as MANUAL or AUTOMATIC.
    mode: []const u8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/OperationalMode";
    /// Upstream `string` constant `MANUAL`.
    pub const MANUAL: []const u8 = "MANUAL";
    /// Upstream `string` constant `AUTOMATIC`.
    pub const AUTOMATIC: []const u8 = "AUTOMATIC";

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!OperationalMode {
        return cdr.decode(OperationalMode, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: OperationalMode) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: OperationalMode, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/ProgramInformation`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/ProgramInformation.msg
pub const ProgramInformation = struct {
    /// Program name returned by the dashboard.
    name: []const u8,
    /// Program description returned by the dashboard.
    description: []const u8,
    /// Creation date as the unsigned value supplied by the dashboard.
    created_date: u64,
    /// Last save date as the unsigned value supplied by the dashboard.
    last_saved_date: u64,
    /// Last modification date as the unsigned value supplied by the dashboard.
    last_modified_date: u64,
    /// Program revision state, such as DRAFT or FINAL.
    program_state: []const u8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/ProgramInformation";
    /// Upstream `string` constant `PROGRAM_STATE_DRAFT`.
    pub const PROGRAM_STATE_DRAFT: []const u8 = "DRAFT";
    /// Upstream `string` constant `PROGRAM_STATE_FINAL`.
    pub const PROGRAM_STATE_FINAL: []const u8 = "FINAL";

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!ProgramInformation {
        return cdr.decode(ProgramInformation, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: ProgramInformation) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: ProgramInformation, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/ProgramState`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/ProgramState.msg
pub const ProgramState = struct {
    /// Execution state, such as STOPPED, PLAYING or PAUSED.
    state: []const u8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/ProgramState";
    /// Upstream `string` constant `STOPPED`.
    pub const STOPPED: []const u8 = "STOPPED";
    /// Upstream `string` constant `PLAYING`.
    pub const PLAYING: []const u8 = "PLAYING";
    /// Upstream `string` constant `PAUSED`.
    pub const PAUSED: []const u8 = "PAUSED";

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!ProgramState {
        return cdr.decode(ProgramState, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: ProgramState) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: ProgramState, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/RobotMode`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/RobotMode.msg
pub const RobotMode = struct {
    /// Signed robot operating-mode code. NO_CONTROLLER is -1.
    mode: i8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/RobotMode";
    /// Upstream `int8` constant `NO_CONTROLLER`.
    pub const NO_CONTROLLER: i8 = -1;
    /// Upstream `int8` constant `DISCONNECTED`.
    pub const DISCONNECTED: i8 = 0;
    /// Upstream `int8` constant `CONFIRM_SAFETY`.
    pub const CONFIRM_SAFETY: i8 = 1;
    /// Upstream `int8` constant `BOOTING`.
    pub const BOOTING: i8 = 2;
    /// Upstream `int8` constant `POWER_OFF`.
    pub const POWER_OFF: i8 = 3;
    /// Upstream `int8` constant `POWER_ON`.
    pub const POWER_ON: i8 = 4;
    /// Upstream `int8` constant `IDLE`.
    pub const IDLE: i8 = 5;
    /// Upstream `int8` constant `BACKDRIVE`.
    pub const BACKDRIVE: i8 = 6;
    /// Upstream `int8` constant `RUNNING`.
    pub const RUNNING: i8 = 7;
    /// Upstream `int8` constant `UPDATING_FIRMWARE`.
    pub const UPDATING_FIRMWARE: i8 = 8;

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!RobotMode {
        return cdr.decode(RobotMode, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: RobotMode) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: RobotMode, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/SafetyMode`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/SafetyMode.msg
pub const SafetyMode = struct {
    /// Unsigned safety-mode code reported by the dashboard.
    mode: u8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/SafetyMode";
    /// Upstream `uint8` constant `NORMAL`.
    pub const NORMAL: u8 = 1;
    /// Upstream `uint8` constant `REDUCED`.
    pub const REDUCED: u8 = 2;
    /// Upstream `uint8` constant `PROTECTIVE_STOP`.
    pub const PROTECTIVE_STOP: u8 = 3;
    /// Upstream `uint8` constant `RECOVERY`.
    pub const RECOVERY: u8 = 4;
    /// Upstream `uint8` constant `SAFEGUARD_STOP`.
    pub const SAFEGUARD_STOP: u8 = 5;
    /// Upstream `uint8` constant `SYSTEM_EMERGENCY_STOP`.
    pub const SYSTEM_EMERGENCY_STOP: u8 = 6;
    /// Upstream `uint8` constant `ROBOT_EMERGENCY_STOP`.
    pub const ROBOT_EMERGENCY_STOP: u8 = 7;
    /// Upstream `uint8` constant `VIOLATION`.
    pub const VIOLATION: u8 = 8;
    /// Upstream `uint8` constant `FAULT`.
    pub const FAULT: u8 = 9;
    /// Upstream `uint8` constant `VALIDATE_JOINT_ID`.
    pub const VALIDATE_JOINT_ID: u8 = 10;
    /// Upstream `uint8` constant `UNDEFINED_SAFETY_MODE`.
    pub const UNDEFINED_SAFETY_MODE: u8 = 11;
    /// Upstream `uint8` constant `AUTOMATIC_MODE_SAFEGUARD_STOP`.
    pub const AUTOMATIC_MODE_SAFEGUARD_STOP: u8 = 12;
    /// Upstream `uint8` constant `SYSTEM_THREE_POSITION_ENABLING_STOP`.
    pub const SYSTEM_THREE_POSITION_ENABLING_STOP: u8 = 13;

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!SafetyMode {
        return cdr.decode(SafetyMode, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: SafetyMode) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: SafetyMode, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/SafetyStatus`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/SafetyStatus.msg
pub const SafetyStatus = struct {
    /// Signed safety-status code reported by the dashboard.
    status: i8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/SafetyStatus";
    /// Upstream `int8` constant `NORMAL`.
    pub const NORMAL: i8 = 1;
    /// Upstream `int8` constant `REDUCED`.
    pub const REDUCED: i8 = 2;
    /// Upstream `int8` constant `PROTECTIVE_STOP`.
    pub const PROTECTIVE_STOP: i8 = 3;
    /// Upstream `int8` constant `RECOVERY`.
    pub const RECOVERY: i8 = 4;
    /// Upstream `int8` constant `SAFEGUARD_STOP`.
    pub const SAFEGUARD_STOP: i8 = 5;
    /// Upstream `int8` constant `SYSTEM_EMERGENCY_STOP`.
    pub const SYSTEM_EMERGENCY_STOP: i8 = 6;
    /// Upstream `int8` constant `ROBOT_EMERGENCY_STOP`.
    pub const ROBOT_EMERGENCY_STOP: i8 = 7;
    /// Upstream `int8` constant `VIOLATION`.
    pub const VIOLATION: i8 = 8;
    /// Upstream `int8` constant `FAULT`.
    pub const FAULT: i8 = 9;
    /// Upstream `int8` constant `VALIDATE_JOINT_ID`.
    pub const VALIDATE_JOINT_ID: i8 = 10;
    /// Upstream `int8` constant `UNDEFINED_SAFETY_MODE`.
    pub const UNDEFINED_SAFETY_MODE: i8 = 11;
    /// Upstream `int8` constant `AUTOMATIC_MODE_SAFEGUARD_STOP`.
    pub const AUTOMATIC_MODE_SAFEGUARD_STOP: i8 = 12;
    /// Upstream `int8` constant `SYSTEM_THREE_POSITION_ENABLING_STOP`.
    pub const SYSTEM_THREE_POSITION_ENABLING_STOP: i8 = 13;
    /// Upstream `int8` constant `TP_THREE_POSITION_ENABLING_STOP`.
    pub const TP_THREE_POSITION_ENABLING_STOP: i8 = 14;
    /// Upstream `int8` constant `IMMI_EMERGENCY_STOP`.
    pub const IMMI_EMERGENCY_STOP: i8 = 15;
    /// Upstream `int8` constant `IMMI_SAFEGUARD_STOP`.
    pub const IMMI_SAFEGUARD_STOP: i8 = 16;
    /// Upstream `int8` constant `PROFISAFE_WAITING_FOR_PARAMETERS`.
    pub const PROFISAFE_WAITING_FOR_PARAMETERS: i8 = 17;
    /// Upstream `int8` constant `PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP`.
    pub const PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP: i8 = 18;
    /// Upstream `int8` constant `PROFISAFE_SAFEGUARD_STOP`.
    pub const PROFISAFE_SAFEGUARD_STOP: i8 = 19;
    /// Upstream `int8` constant `PROFISAFE_EMERGENCY_STOP`.
    pub const PROFISAFE_EMERGENCY_STOP: i8 = 20;
    /// Upstream `int8` constant `SAFETY_API_SAFEGUARD_STOP`.
    pub const SAFETY_API_SAFEGUARD_STOP: i8 = 22;
    /// Upstream `int8` constant `IO_PLANE_STOP`.
    pub const IO_PLANE_STOP: i8 = 23;

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!SafetyStatus {
        return cdr.decode(SafetyStatus, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: SafetyStatus) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: SafetyStatus, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/UserRole`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/UserRole.msg
pub const UserRole = struct {
    /// User role reported by the dashboard.
    role: []const u8,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/UserRole";
    /// Upstream `string` constant `PROGRAMMER`.
    pub const PROGRAMMER: []const u8 = "PROGRAMMER";
    /// Upstream `string` constant `OPERATOR`.
    pub const OPERATOR: []const u8 = "OPERATOR";
    /// Upstream `string` constant `NONE`.
    pub const NONE: []const u8 = "NONE";
    /// Upstream `string` constant `LOCKED`.
    pub const LOCKED: []const u8 = "LOCKED";
    /// Upstream `string` constant `RESTRICTED`.
    pub const RESTRICTED: []const u8 = "RESTRICTED";

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!UserRole {
        return cdr.decode(UserRole, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: UserRole) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: UserRole, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};

/// `ur_dashboard_msgs/msg/VersionInformation`.
/// Upstream definition at https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg/VersionInformation.msg
pub const VersionInformation = struct {
    /// PolyScope major version number.
    major: u32,
    /// PolyScope minor version number.
    minor: u32,
    /// PolyScope bugfix version number.
    bugfix: u32,
    /// PolyScope build number.
    build: u32,

    /// Fully qualified ROS 2 type name.
    pub const ros_type = "ur_dashboard_msgs/msg/VersionInformation";

    /// Decode one complete encapsulated message. Strings borrow the frame bytes.
    pub fn decode(frame: []const u8) Error!VersionInformation {
        return cdr.decode(VersionInformation, frame);
    }

    /// Check the framing, field lengths, alignment and end of the message.
    pub fn validate(frame: []const u8) Error!void {
        _ = try decode(frame);
    }

    /// Number of bytes needed for canonical framing, including the encapsulation.
    pub fn encodedSize(self: VersionInformation) Error!usize {
        return cdr.encodedSize(self);
    }

    /// Encode in caller-owned storage. A short destination remains untouched.
    pub fn encode(self: VersionInformation, order: Endian, out: []u8) Error!usize {
        return cdr.encode(self, order, out);
    }
};
