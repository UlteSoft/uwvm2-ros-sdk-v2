"""Unitree ROS 2 v0.3.0 unitree_api message definitions."""
from unitree_cdr import Message


class Request(Message):
    """unitree_api/msg/Request in ROS field order."""
    __slots__ = ('header', 'parameter', 'binary')
    _fields = (
        ('header', 'RequestHeader', None),
        ('parameter', 'string', None),
        ('binary', 'uint8', -1),
    )


class RequestHeader(Message):
    """unitree_api/msg/RequestHeader in ROS field order."""
    __slots__ = ('identity', 'lease', 'policy')
    _fields = (
        ('identity', 'RequestIdentity', None),
        ('lease', 'RequestLease', None),
        ('policy', 'RequestPolicy', None),
    )


class RequestIdentity(Message):
    """unitree_api/msg/RequestIdentity in ROS field order."""
    __slots__ = ('id', 'api_id')
    _fields = (
        ('id', 'int64', None),
        ('api_id', 'int64', None),
    )


class RequestLease(Message):
    """unitree_api/msg/RequestLease in ROS field order."""
    __slots__ = ('id',)
    _fields = (
        ('id', 'int64', None),
    )


class RequestPolicy(Message):
    """unitree_api/msg/RequestPolicy in ROS field order."""
    __slots__ = ('priority', 'noreply')
    _fields = (
        ('priority', 'int32', None),
        ('noreply', 'bool', None),
    )


class Response(Message):
    """unitree_api/msg/Response in ROS field order."""
    __slots__ = ('header', 'data', 'binary')
    _fields = (
        ('header', 'ResponseHeader', None),
        ('data', 'string', None),
        ('binary', 'int8', -1),
    )


class ResponseHeader(Message):
    """unitree_api/msg/ResponseHeader in ROS field order."""
    __slots__ = ('identity', 'status')
    _fields = (
        ('identity', 'RequestIdentity', None),
        ('status', 'ResponseStatus', None),
    )


class ResponseStatus(Message):
    """unitree_api/msg/ResponseStatus in ROS field order."""
    __slots__ = ('code',)
    _fields = (
        ('code', 'int32', None),
    )
