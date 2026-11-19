//! Query the installed ROS ABI before starting the controller.
extern "uwvm_ros_v2" fn abi() u32;

export fn _start() void {
    if (abi() != 2) @trap();
}
