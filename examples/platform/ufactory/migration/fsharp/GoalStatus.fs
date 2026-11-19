// @file GoalStatus.fs
// @brief Interpret ROS 1 actionlib GoalStatus wire values inside a Wasm guest.
module GoalStatus

/// @brief Check every wire status using the client terminal-state semantics.
/// @param abi Scene ABI supplied by the VM. It also rotates the test input order.
/// @return Zero for ABI 2 and the exact set of terminal wire values.
let Check (abi: int) =
    let mutable mask = 0
    let first = abi &&& 7
    let mutable value = first
    let mutable count = 0
    while count = 0 || value <> first do
        // PREEMPTED, SUCCEEDED, ABORTED, REJECTED, RECALLED and client-local LOST.
        if (value >= 2 && value <= 5) || value = 8 || value = 9 then
            mask <- mask ||| (1 <<< value)
        value <- if value = 9 then 0 else value + 1
        count <- count + 1
    if abi = 2 && mask = 828 then 0 else 1

/// @brief Read the granted scene ABI and run the application assertion.
let Start () = Check (Wros.Scene.Abi())
