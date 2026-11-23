"""Unitree ROS 2 v0.3.0 unitree_go message definitions."""
from unitree_cdr import Message


class AudioData(Message):
    """unitree_go/msg/AudioData in ROS field order."""
    __slots__ = ('time_frame', 'data')
    _fields = (
        ('time_frame', 'uint64', None),
        ('data', 'uint8', -1),
    )


class BmsCmd(Message):
    """unitree_go/msg/BmsCmd in ROS field order."""
    __slots__ = ('off', 'reserve')
    _fields = (
        ('off', 'uint8', None),
        ('reserve', 'uint8', 3),
    )


class BmsState(Message):
    """unitree_go/msg/BmsState in ROS field order."""
    __slots__ = ('version_high', 'version_low', 'status', 'soc', 'current', 'cycle', 'bq_ntc', 'mcu_ntc', 'cell_vol')
    _fields = (
        ('version_high', 'uint8', None),
        ('version_low', 'uint8', None),
        ('status', 'uint8', None),
        ('soc', 'uint8', None),
        ('current', 'int32', None),
        ('cycle', 'uint16', None),
        ('bq_ntc', 'int8', 2),
        ('mcu_ntc', 'int8', 2),
        ('cell_vol', 'uint16', 15),
    )


class Error(Message):
    """unitree_go/msg/Error in ROS field order."""
    __slots__ = ('source', 'state')
    _fields = (
        ('source', 'uint32', None),
        ('state', 'uint32', None),
    )


class Go2FrontVideoData(Message):
    """unitree_go/msg/Go2FrontVideoData in ROS field order."""
    __slots__ = ('time_frame', 'video720p', 'video360p', 'video180p')
    _fields = (
        ('time_frame', 'uint64', None),
        ('video720p', 'uint8', -1),
        ('video360p', 'uint8', -1),
        ('video180p', 'uint8', -1),
    )


class HeightMap(Message):
    """unitree_go/msg/HeightMap in ROS field order."""
    __slots__ = ('stamp', 'frame_id', 'resolution', 'width', 'height', 'origin', 'data')
    _fields = (
        ('stamp', 'float64', None),
        ('frame_id', 'string', None),
        ('resolution', 'float32', None),
        ('width', 'uint32', None),
        ('height', 'uint32', None),
        ('origin', 'float32', 2),
        ('data', 'float32', -1),
    )


class IMUState(Message):
    """unitree_go/msg/IMUState in ROS field order."""
    __slots__ = ('quaternion', 'gyroscope', 'accelerometer', 'rpy', 'temperature')
    _fields = (
        ('quaternion', 'float32', 4),
        ('gyroscope', 'float32', 3),
        ('accelerometer', 'float32', 3),
        ('rpy', 'float32', 3),
        ('temperature', 'int8', None),
    )


class InterfaceConfig(Message):
    """unitree_go/msg/InterfaceConfig in ROS field order."""
    __slots__ = ('mode', 'value', 'reserve')
    _fields = (
        ('mode', 'uint8', None),
        ('value', 'uint8', None),
        ('reserve', 'uint8', 2),
    )


class LidarState(Message):
    """unitree_go/msg/LidarState in ROS field order."""
    __slots__ = ('stamp', 'firmware_version', 'software_version', 'sdk_version', 'sys_rotation_speed', 'com_rotation_speed', 'error_state', 'cloud_frequency', 'cloud_packet_loss_rate', 'cloud_size', 'cloud_scan_num', 'imu_frequency', 'imu_packet_loss_rate', 'imu_rpy', 'serial_recv_stamp', 'serial_buffer_size', 'serial_buffer_read')
    _fields = (
        ('stamp', 'float64', None),
        ('firmware_version', 'string', None),
        ('software_version', 'string', None),
        ('sdk_version', 'string', None),
        ('sys_rotation_speed', 'float32', None),
        ('com_rotation_speed', 'float32', None),
        ('error_state', 'uint8', None),
        ('cloud_frequency', 'float32', None),
        ('cloud_packet_loss_rate', 'float32', None),
        ('cloud_size', 'uint32', None),
        ('cloud_scan_num', 'uint32', None),
        ('imu_frequency', 'float32', None),
        ('imu_packet_loss_rate', 'float32', None),
        ('imu_rpy', 'float32', 3),
        ('serial_recv_stamp', 'float64', None),
        ('serial_buffer_size', 'uint32', None),
        ('serial_buffer_read', 'uint32', None),
    )


class LowCmd(Message):
    """unitree_go/msg/LowCmd in ROS field order."""
    __slots__ = ('head', 'level_flag', 'frame_reserve', 'sn', 'version', 'bandwidth', 'motor_cmd', 'bms_cmd', 'wireless_remote', 'led', 'fan', 'gpio', 'reserve', 'crc')
    _fields = (
        ('head', 'uint8', 2),
        ('level_flag', 'uint8', None),
        ('frame_reserve', 'uint8', None),
        ('sn', 'uint32', 2),
        ('version', 'uint32', 2),
        ('bandwidth', 'uint16', None),
        ('motor_cmd', 'MotorCmd', 20),
        ('bms_cmd', 'BmsCmd', None),
        ('wireless_remote', 'uint8', 40),
        ('led', 'uint8', 12),
        ('fan', 'uint8', 2),
        ('gpio', 'uint8', None),
        ('reserve', 'uint32', None),
        ('crc', 'uint32', None),
    )


class LowState(Message):
    """unitree_go/msg/LowState in ROS field order."""
    __slots__ = ('head', 'level_flag', 'frame_reserve', 'sn', 'version', 'bandwidth', 'imu_state', 'motor_state', 'bms_state', 'foot_force', 'foot_force_est', 'tick', 'wireless_remote', 'bit_flag', 'adc_reel', 'temperature_ntc1', 'temperature_ntc2', 'power_v', 'power_a', 'fan_frequency', 'reserve', 'crc')
    _fields = (
        ('head', 'uint8', 2),
        ('level_flag', 'uint8', None),
        ('frame_reserve', 'uint8', None),
        ('sn', 'uint32', 2),
        ('version', 'uint32', 2),
        ('bandwidth', 'uint16', None),
        ('imu_state', 'IMUState', None),
        ('motor_state', 'MotorState', 20),
        ('bms_state', 'BmsState', None),
        ('foot_force', 'int16', 4),
        ('foot_force_est', 'int16', 4),
        ('tick', 'uint32', None),
        ('wireless_remote', 'uint8', 40),
        ('bit_flag', 'uint8', None),
        ('adc_reel', 'float32', None),
        ('temperature_ntc1', 'int8', None),
        ('temperature_ntc2', 'int8', None),
        ('power_v', 'float32', None),
        ('power_a', 'float32', None),
        ('fan_frequency', 'uint16', 4),
        ('reserve', 'uint32', None),
        ('crc', 'uint32', None),
    )


class MotorCmd(Message):
    """unitree_go/msg/MotorCmd in ROS field order."""
    __slots__ = ('mode', 'q', 'dq', 'tau', 'kp', 'kd', 'reserve')
    _fields = (
        ('mode', 'uint8', None),
        ('q', 'float32', None),
        ('dq', 'float32', None),
        ('tau', 'float32', None),
        ('kp', 'float32', None),
        ('kd', 'float32', None),
        ('reserve', 'uint32', 3),
    )


class MotorCmds(Message):
    """unitree_go/msg/MotorCmds in ROS field order."""
    __slots__ = ('cmds',)
    _fields = (
        ('cmds', 'MotorCmd', -1),
    )


class MotorState(Message):
    """unitree_go/msg/MotorState in ROS field order."""
    __slots__ = ('mode', 'q', 'dq', 'ddq', 'tau_est', 'q_raw', 'dq_raw', 'ddq_raw', 'temperature', 'lost', 'reserve')
    _fields = (
        ('mode', 'uint8', None),
        ('q', 'float32', None),
        ('dq', 'float32', None),
        ('ddq', 'float32', None),
        ('tau_est', 'float32', None),
        ('q_raw', 'float32', None),
        ('dq_raw', 'float32', None),
        ('ddq_raw', 'float32', None),
        ('temperature', 'int8', None),
        ('lost', 'uint32', None),
        ('reserve', 'uint32', 2),
    )


class MotorStates(Message):
    """unitree_go/msg/MotorStates in ROS field order."""
    __slots__ = ('states',)
    _fields = (
        ('states', 'MotorState', -1),
    )


class PathPoint(Message):
    """unitree_go/msg/PathPoint in ROS field order."""
    __slots__ = ('t_from_start', 'x', 'y', 'yaw', 'vx', 'vy', 'vyaw')
    _fields = (
        ('t_from_start', 'float32', None),
        ('x', 'float32', None),
        ('y', 'float32', None),
        ('yaw', 'float32', None),
        ('vx', 'float32', None),
        ('vy', 'float32', None),
        ('vyaw', 'float32', None),
    )


class Req(Message):
    """unitree_go/msg/Req in ROS field order."""
    __slots__ = ('uuid', 'body')
    _fields = (
        ('uuid', 'string', None),
        ('body', 'string', None),
    )


class Res(Message):
    """unitree_go/msg/Res in ROS field order."""
    __slots__ = ('uuid', 'data', 'body')
    _fields = (
        ('uuid', 'string', None),
        ('data', 'uint8', -1),
        ('body', 'string', None),
    )


class SportModeCmd(Message):
    """unitree_go/msg/SportModeCmd in ROS field order."""
    __slots__ = ('mode', 'gait_type', 'speed_level', 'foot_raise_height', 'body_height', 'position', 'euler', 'velocity', 'yaw_speed', 'bms_cmd', 'path_point')
    _fields = (
        ('mode', 'uint8', None),
        ('gait_type', 'uint8', None),
        ('speed_level', 'uint8', None),
        ('foot_raise_height', 'float32', None),
        ('body_height', 'float32', None),
        ('position', 'float32', 2),
        ('euler', 'float32', 3),
        ('velocity', 'float32', 2),
        ('yaw_speed', 'float32', None),
        ('bms_cmd', 'BmsCmd', None),
        ('path_point', 'PathPoint', 30),
    )


class SportModeState(Message):
    """unitree_go/msg/SportModeState in ROS field order."""
    __slots__ = ('stamp', 'error_code', 'imu_state', 'mode', 'progress', 'gait_type', 'foot_raise_height', 'position', 'body_height', 'velocity', 'yaw_speed', 'range_obstacle', 'foot_force', 'foot_position_body', 'foot_speed_body')
    _fields = (
        ('stamp', 'TimeSpec', None),
        ('error_code', 'uint32', None),
        ('imu_state', 'IMUState', None),
        ('mode', 'uint8', None),
        ('progress', 'float32', None),
        ('gait_type', 'uint8', None),
        ('foot_raise_height', 'float32', None),
        ('position', 'float32', 3),
        ('body_height', 'float32', None),
        ('velocity', 'float32', 3),
        ('yaw_speed', 'float32', None),
        ('range_obstacle', 'float32', 4),
        ('foot_force', 'int16', 4),
        ('foot_position_body', 'float32', 12),
        ('foot_speed_body', 'float32', 12),
    )


class TimeSpec(Message):
    """unitree_go/msg/TimeSpec in ROS field order."""
    __slots__ = ('sec', 'nanosec')
    _fields = (
        ('sec', 'int32', None),
        ('nanosec', 'uint32', None),
    )


class UwbState(Message):
    """unitree_go/msg/UwbState in ROS field order."""
    __slots__ = ('version', 'channel', 'joy_mode', 'orientation_est', 'pitch_est', 'distance_est', 'yaw_est', 'tag_roll', 'tag_pitch', 'tag_yaw', 'base_roll', 'base_pitch', 'base_yaw', 'joystick', 'error_state', 'buttons', 'enabled_from_app')
    _fields = (
        ('version', 'uint8', 2),
        ('channel', 'uint8', None),
        ('joy_mode', 'uint8', None),
        ('orientation_est', 'float32', None),
        ('pitch_est', 'float32', None),
        ('distance_est', 'float32', None),
        ('yaw_est', 'float32', None),
        ('tag_roll', 'float32', None),
        ('tag_pitch', 'float32', None),
        ('tag_yaw', 'float32', None),
        ('base_roll', 'float32', None),
        ('base_pitch', 'float32', None),
        ('base_yaw', 'float32', None),
        ('joystick', 'float32', 2),
        ('error_state', 'uint8', None),
        ('buttons', 'uint8', None),
        ('enabled_from_app', 'uint8', None),
    )


class UwbSwitch(Message):
    """unitree_go/msg/UwbSwitch in ROS field order."""
    __slots__ = ('enabled',)
    _fields = (
        ('enabled', 'uint8', None),
    )


class WirelessController(Message):
    """unitree_go/msg/WirelessController in ROS field order."""
    __slots__ = ('lx', 'ly', 'rx', 'ry', 'keys')
    _fields = (
        ('lx', 'float32', None),
        ('ly', 'float32', None),
        ('rx', 'float32', None),
        ('ry', 'float32', None),
        ('keys', 'uint16', None),
    )
