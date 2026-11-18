-- Build this example with --ros-abi. The only ROS import is uwvm_ros_v2.abi.
assert(wros.abi() == 2)

local measurements = {0.75, 0.25, 0.5}
table.sort(measurements)
assert(string.format("%.2f", measurements[2]) == "0.50")
