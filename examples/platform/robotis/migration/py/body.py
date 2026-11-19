"""@brief Preserve geometry_msgs/Twist field order and six float64 values across ROS1 and little-endian CDR."""
import _struct

# geometry_msgs/Twist.msg declares Vector3 linear followed by Vector3 angular.
# Each Vector3.msg declares float64 x, y and z in this order.
ros1 = bytes.fromhex("000000000000f03f00000000000000c00000000000000c40"
                     "000000000000e03f000000000000000000000000000004c0")
values = _struct.unpack("<6d", ros1)
assert values == (1.0, -2.0, 3.5, 0.5, 0.0, -2.5)
cdr = b"\x00\x01\x00\x00" + _struct.pack("<6d", *values)
assert len(cdr) == 52 and cdr[4:] == ros1
assert _struct.unpack("<6d", cdr[4:]) == values
