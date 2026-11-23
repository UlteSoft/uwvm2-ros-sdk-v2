"""Unitree ROS 2 v0.3.0 unitree_hg message definitions."""
from unitree_cdr import Message


class BmsCmd(Message):
    """unitree_hg/msg/BmsCmd in ROS field order."""
    __slots__ = ('cmd', 'reserve')
    _fields = (
        ('cmd', 'uint8', None),
        ('reserve', 'uint8', 40),
    )


class BmsState(Message):
    """unitree_hg/msg/BmsState in ROS field order."""
    __slots__ = ('version_high', 'version_low', 'fn', 'cell_vol', 'bmsvoltage', 'current', 'soc', 'soh', 'temperature', 'cycle', 'manufacturer_date', 'bmsstate', 'reserve')
    _fields = (
        ('version_high', 'uint8', None),
        ('version_low', 'uint8', None),
        ('fn', 'uint8', None),
        ('cell_vol', 'uint16', 40),
        ('bmsvoltage', 'uint32', 3),
        ('current', 'int32', None),
        ('soc', 'uint8', None),
        ('soh', 'uint8', None),
        ('temperature', 'int16', 12),
        ('cycle', 'uint16', None),
        ('manufacturer_date', 'uint16', None),
        ('bmsstate', 'uint32', 5),
        ('reserve', 'uint32', 3),
    )


class HandCmd(Message):
    """unitree_hg/msg/HandCmd in ROS field order."""
    __slots__ = ('motor_cmd', 'reserve')
    _fields = (
        ('motor_cmd', 'MotorCmd', -1),
        ('reserve', 'uint32', 4),
    )


class HandState(Message):
    """unitree_hg/msg/HandState in ROS field order."""
    __slots__ = ('motor_state', 'press_sensor_state', 'imu_state', 'power_v', 'power_a', 'system_v', 'device_v', 'error', 'reserve')
    _fields = (
        ('motor_state', 'MotorState', -1),
        ('press_sensor_state', 'PressSensorState', -1),
        ('imu_state', 'IMUState', None),
        ('power_v', 'float32', None),
        ('power_a', 'float32', None),
        ('system_v', 'float32', None),
        ('device_v', 'float32', None),
        ('error', 'uint32', 2),
        ('reserve', 'uint32', 2),
    )


class IMUState(Message):
    """unitree_hg/msg/IMUState in ROS field order."""
    __slots__ = ('quaternion', 'gyroscope', 'accelerometer', 'rpy', 'temperature')
    _fields = (
        ('quaternion', 'float32', 4),
        ('gyroscope', 'float32', 3),
        ('accelerometer', 'float32', 3),
        ('rpy', 'float32', 3),
        ('temperature', 'int16', None),
    )


class LowCmd(Message):
    """unitree_hg/msg/LowCmd in ROS field order."""
    __slots__ = ('mode_pr', 'mode_machine', 'motor_cmd', 'reserve', 'crc')
    _fields = (
        ('mode_pr', 'uint8', None),
        ('mode_machine', 'uint8', None),
        ('motor_cmd', 'MotorCmd', 35),
        ('reserve', 'uint32', 4),
        ('crc', 'uint32', None),
    )


class LowState(Message):
    """unitree_hg/msg/LowState in ROS field order."""
    __slots__ = ('version', 'mode_pr', 'mode_machine', 'tick', 'imu_state', 'motor_state', 'wireless_remote', 'reserve', 'crc')
    _fields = (
        ('version', 'uint32', 2),
        ('mode_pr', 'uint8', None),
        ('mode_machine', 'uint8', None),
        ('tick', 'uint32', None),
        ('imu_state', 'IMUState', None),
        ('motor_state', 'MotorState', 35),
        ('wireless_remote', 'uint8', 40),
        ('reserve', 'uint32', 4),
        ('crc', 'uint32', None),
    )


class MainBoardState(Message):
    """unitree_hg/msg/MainBoardState in ROS field order."""
    __slots__ = ('fan_state', 'temperature', 'value', 'state')
    _fields = (
        ('fan_state', 'uint16', 6),
        ('temperature', 'int16', 6),
        ('value', 'float32', 6),
        ('state', 'uint32', 6),
    )


class MotorCmd(Message):
    """unitree_hg/msg/MotorCmd in ROS field order."""
    __slots__ = ('mode', 'q', 'dq', 'tau', 'kp', 'kd', 'reserve')
    _fields = (
        ('mode', 'uint8', None),
        ('q', 'float32', None),
        ('dq', 'float32', None),
        ('tau', 'float32', None),
        ('kp', 'float32', None),
        ('kd', 'float32', None),
        ('reserve', 'uint32', None),
    )


class MotorState(Message):
    """unitree_hg/msg/MotorState in ROS field order."""
    __slots__ = ('mode', 'q', 'dq', 'ddq', 'tau_est', 'temperature', 'vol', 'sensor', 'motorstate', 'reserve')
    _fields = (
        ('mode', 'uint8', None),
        ('q', 'float32', None),
        ('dq', 'float32', None),
        ('ddq', 'float32', None),
        ('tau_est', 'float32', None),
        ('temperature', 'int16', 2),
        ('vol', 'float32', None),
        ('sensor', 'uint32', 2),
        ('motorstate', 'uint32', None),
        ('reserve', 'uint32', 4),
    )


class PressSensorState(Message):
    """unitree_hg/msg/PressSensorState in ROS field order."""
    __slots__ = ('pressure', 'temperature', 'lost', 'reserve')
    _fields = (
        ('pressure', 'float32', 12),
        ('temperature', 'float32', 12),
        ('lost', 'uint32', None),
        ('reserve', 'uint32', None),
    )
