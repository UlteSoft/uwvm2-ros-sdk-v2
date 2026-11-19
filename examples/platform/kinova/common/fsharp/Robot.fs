// @file Robot.fs
// @brief Query the VM scene ABI using an operator-granted import.
module Robot

/// @brief Accept the ABI understood by this example.
/// @param version ABI number returned by the scene host.
/// @return Zero to continue or one to stop the guest.
let Policy (version: int) =
    if version = 2 then 0 else 1

/// @brief Invoke the sole requested ROS operation and check its result.
let Start () =
    Policy (Wros.Scene.Abi())
